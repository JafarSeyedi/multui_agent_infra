# Effort and cost of expressing that logic
Formily is a powerhouse for data-driven, enterprise forms. Its declarative x-reactions system and schema-driven architecture are unmatched for complex logic in JSON. However, the main limitations you might face are not in the logic it can express, but in the effort and cost of expressing that logic, particularly in three specific areas:

- Highly Custom UI Components: Formily requires a specific adapter to integrate custom React components. If your design system requires a truly unique or highly interactive component, making it "Formily-ready" takes more upfront work than simply dropping it into RHF.

- Extreme Custom Layouts: Some highly unique layouts or UI paradigms (like the intricate Table+Form matrix described in a challenge) can be complex to represent purely in schema, sometimes requiring deep knowledge of Formily's internals. In such cases, a more direct, imperative approach might be faster.

The "Designer Gap" & Learning Curve: Formily's powerful visual designer doesn't always natively support custom components, requiring manual schema adjustments. If your team includes members less familiar with Formily’s model, the learning curve can slow down initial development.

# Strategy 1: Feature-based isolation 

This approach separates RHF and Formily by feature type. It provides the clearest separation of concerns:
- Unified approach where Formily is used for all forms, eliminating the need for RHF, unless a scenario arises that proves prohibitively complex.
-  Formily for all forms as the default (including simple ones). Your backup plan to use RHF only if the team hits a "wall" where building the form is not feasible in Formily.

This separation works cleanly because each library is used only where its strengths align.

# Strategy 2: The "Migration Layer" Strategy

This strategy helps with gradually moving an existing project from Formily to RHF or vice-versa:

- Wrap each Formily form in a dedicated <FormilyWrapper> component.
- Wrap each React Hook Form in a dedicated <RHFWrapper> component.

This isolates each library's providers and prevents context conflicts.

# Strategy 3: Leveraging the ecosystem

This approach embraces both libraries together for maximum flexibility:

- Use Formily for building schema-driven, dynamic forms coming from your backend.
- Use RHF for common UI patterns like FilterBar, SearchBox, or standalone FieldArray components.
- Manage Formily Widgets that internally use RHF. This is an advanced pattern that keeps the schema unchanged while gaining access to RHF's powerful hooks for complex business logic.