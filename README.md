# Reliable Multi-Step Operations

A problem definition. No solution, no architecture, no technology choices — those are the
work.

---

## 1. Context

A single user-facing action often requires several things to happen across several
independent systems. Each of those systems has its own database, its own availability, and
its own idea of what "committed" means. None of them share a transaction.

When all the steps succeed, this is invisible. The difficulty is everything else: a step
that fails, a step whose outcome is unknown, a process that dies halfway through, a network
that swallows a request and delivers it twice.

The naive version of this — call service A, then B, then C, and hope — works in
development and fails in production in ways that are quiet, delayed, and expensive. It
leaves rooms reserved for bookings that don't exist, customers charged for accounts that
were never created, and resources provisioned that nothing will ever clean up.

## 2. The problem

Build a system that executes an ordered sequence of steps across independent services and
guarantees that every request reaches a **defined terminal state** — either fully applied,
or unwound so that no lasting effect remains — regardless of where in the sequence
something goes wrong, and regardless of whether the system executing it crashes partway.

The central constraint that makes this hard:

> **Steps commit immediately and independently. There is nothing to roll back to.**

By the time step 4 fails, steps 1 through 3 are durable in three other systems that have
never heard of your request. The only way to "undo" them is to perform new actions that
counteract them — release the reservation, refund the payment, delete the resource. These
undo actions are themselves network calls to unreliable services, and they can fail too.

A second constraint follows from the first:

> **Some effects cannot be undone at all.**

An email has been read. A webhook has fired and a downstream partner has acted on it. A
notification has appeared on someone's phone. The system must recognise which steps are
reversible and which are not, and must never place itself in a position where it needs to
reverse something that can't be.

## 3. Worked example

Provisioning a new customer workspace. Five steps across five systems, none of which commit
together — each one is durable the moment it returns, and no transaction spans any two of
them.

| # | Step | Undo action | Notes |
|---|------|-------------|-------|
| 1 | Create the workspace record | Delete it | Fully reversible, internal |
| 2 | Claim the customer's chosen subdomain in a global registry | Release the claim | Reversible, but contended — two customers may want the same one |
| 3 | Create a billing customer and charge the first month | Refund the charge | Reversible, but the customer sees both lines on their statement |
| 4 | Provision dedicated storage | Deprovision it | Slow — may take minutes |
| 5 | Send the welcome email | **None** | Irreversible |

Two properties of this sequence matter more than the details:

**Step 3 is the point of no return.** Before money moves, everything is a reversible hold
and abandoning the request is cheap. After money moves, unwinding means refunding a
customer who asked for the service and might well get it if you just retried. The system
needs a position on where this line sits and what changes when it's crossed.

**Step 5 cannot be undone.** So it must not be possible for the request to fail *after*
step 5 in a way that requires undoing it. Ordering is not arbitrary — irreversibility
constrains it.

## 4. Scenarios

These are the cases the design must answer. A design that handles eight of them and not the
ninth is the wrong design, and the ninth is usually where the real data loss lives.

### 4.1 Everything succeeds
Steps 1–5 complete. The request is done. Nothing interesting here except that "done" must
be recorded durably and must be queryable afterwards.

### 4.2 A step fails cleanly, before the point of no return
Step 2 returns an explicit "that subdomain is taken." Nothing was committed. Step 1 must be
undone. The request ends in a terminal failed state and the customer is told why.

*The question this raises:* does the undo run in reverse order, and does it have to?

### 4.3 A step's outcome is unknown
Step 2 times out. The registry may have claimed the subdomain, or may not have. The request
cannot proceed, but it also cannot assume nothing happened.

This is the scenario that breaks naive designs. There is no way to find out what happened —
asking the registry is another call that can also time out, and its answer can be stale by
the time it arrives. The system must act correctly *without knowing*, which means undo
actions have to be safe to run against a step that never took effect.

*The question this raises:* what must be recorded, and at what moment, so that after a
restart the system knows a step *may* have had an effect?

### 4.4 A step fails after the point of no return
Payment succeeded; storage provisioning fails. Unwinding now means refunding a customer who
still wants the product. Retrying means the request stays open, possibly for a long time,
possibly forever.

*The question this raises:* is "keep retrying" a terminal state? If not, what bounds it, and
what happens when the bound is hit?

### 4.5 An undo action fails
Payment must be refunded, and the billing provider is down. The request is now neither
applied nor unwound.

This state exists in every real system of this kind, and it cannot be designed away — it can
only be made visible. The system needs a terminal state that means "stuck, human required,"
and it must be impossible to reach that state silently.

### 4.6 The system crashes mid-request
The process executing the sequence dies. It may die:

- before a step is attempted,
- after recording an intention to attempt it but before the call,
- after the call but before the response arrives,
- after the response arrives but before recording it,
- during an undo action, at any of the same points.

On restart, the request must resume and reach a correct terminal state. Every one of these
crash points must be safe. Note that two of them are indistinguishable from 4.3 after the
fact — the system's own crash and the network's silence look identical.

### 4.7 The same request is submitted twice
A client times out and retries. Two identical requests arrive. Exactly one workspace must be
created and exactly one charge must be made.

*The question this raises:* what makes two requests "the same," who decides, and how long
must that decision be remembered?

### 4.8 Two different requests contend for the same resource
Two customers claim the same subdomain simultaneously. Both requests are individually valid.
One must win cleanly, and the loser must unwind without disturbing the winner.

### 4.9 A step takes far longer than expected
Storage provisioning normally takes 30 seconds and this time takes 40 minutes. The system
must not conclude prematurely that it failed and start undoing work that is still in
progress — nor may it wait forever.

*The question this raises:* who owns the timeout, and is a timeout a failure or an unknown?
These are not the same thing.

### 4.10 Someone asks about a request that is still running
A support agent looks up the workspace while step 4 is in flight. What do they see? The
workspace record exists (step 1 committed) but the workspace is not usable and might yet be
deleted.

Intermediate states are visible to everyone. The system cannot hide them; it can only
describe them honestly.

### 4.11 The sequence definition changes while requests are in flight
Step 3 is amended, or a step is inserted. Requests started under the old definition are
still running.

*The question this raises:* does a running request follow the definition it started with, or
the current one? Both answers have consequences.

## 5. Required guarantees

1. **Termination.** Every request reaches a terminal state. "Still running after three days"
   is not a terminal state.
2. **No orphaned effects.** The system never leaves an effect in another service that it has
   no record of and will therefore never clean up.
3. **Crash safety.** Failure of the executing process at any point is recoverable without
   human intervention, except where scenario 4.5 applies.
4. **Repeat safety.** Any step or undo action may be executed more than once, because the
   system will sometimes be unable to tell whether it already ran. Doing so must not produce
   a second effect.
5. **Undo safety.** An undo action must succeed even when the thing it is undoing never
   happened.
6. **Observability.** At any moment, the state of any request is queryable, and the history
   of what was attempted is inspectable after the fact.
7. **Honest failure.** A request that cannot be completed or unwound is reported loudly, not
   swallowed or left in limbo.

## 6. Questions the design must answer

Answer these deliberately, and write down the scenario that forced each answer:

- Is the sequence fixed at definition time, or may it branch or run steps in parallel? If
  steps can run in parallel, what does "undo in reverse order" mean?
- What must be durably recorded before a step is attempted, versus after? Why that order?
- How does the system distinguish "this step definitely did not happen" from "this step's
  outcome is unknown" — and should it bother distinguishing them at all?
- Where does the boundary of reversibility sit, and is it a property of the sequence or of
  each step?
- How does step 3 receive a value produced by step 1?
- How many times does an undo action get retried, and what happens after that?
- What does the system tell the outside world about a request in progress?
- How is a request identified such that a retry is recognised as the same request?

## 7. Out of scope

Deliberately excluded, to keep this finishable:

- Distributed transactions, two-phase commit, or anything requiring participant cooperation
  beyond ordinary API calls.
- Multi-tenancy, authentication, and authorisation.
- High throughput. Correctness under failure is the goal; performance is not.
- A user interface beyond a way to inspect request state.
- Cross-region concerns.

## 8. Definition of done

Not "the happy path works." Done means a test harness that:

1. Executes the example sequence against mock services whose failures are injectable —
   clean failure, timeout, success-reported-as-failure, and arbitrary latency.
2. Kills the executing process at **every** point in the sequence, including inside undo
   actions, and asserts that on restart the request reaches a correct terminal state.
3. Submits duplicate and concurrent requests and asserts that effects occur exactly once.
4. Asserts an invariant after every run: for each step, either its effect is present and the
   request is applied, or its effect is absent, or the request is in the stuck state and has
   been reported.

If that harness passes across a large number of randomised failure schedules, the system
works. If it only passes the failures you thought of, it doesn't.
