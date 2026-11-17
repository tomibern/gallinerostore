---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask.

Build the whole piece of work first. Then write its tests once, at the end, at the seams agreed in the spec.

Run typechecking regularly while building, and the tests once at the end: first the new test files, then the full test suite.

Once done, call the Skill tool with "code-review" to review the work.

Commit your work to the current branch.
