## Form

Based on the Kimi Design System Web Form:

- Figma file: `Kimi Design System Web`
- Node: `4005:41374`
- Component group: `Form`

### Contract

Use Form for data entry and submission interfaces inside a Modal or dedicated page. Form organizes labeled input fields, selection groups, and action triggers into a structured vertical layout. Do not use Form for passive content display or for single binary choices — use Dialog for those.

- **Purpose**: Data collection, settings configuration, information submission.
- **Composition**: `Form` (container) + `FormField` (label + input) + `FormSection` (info summary) + `FormRadioGroup` (single-select) + `FormCheckboxGroup` (multi-select). Form only renders a vertical stack of field instances.
- **States**: `default`, `error`, `disabled`, `loading` (when submitting).
- **Content slots**: `title` and `description` (provided by parent Modal), `sections[]` (info blocks), `fields[]` (input rows), `radioGroups[]` and `checkboxGroups[]` (selection rows), `footer` (actions).
- **Container**: Form is typically placed inside a Modal `medium` (`560px`) or `large` (`720px`). On dedicated pages, Form stretches to its parent width.

Do not use Form for navigation, for wizard multi-step flows, or for content that belongs in a dedicated page without a Modal.

### Size And Dimensions

Form container inside Modal `medium`:

| Property | Value |
|----------|------:|
| Content width | `512px` (inherited from Modal medium padding) |
| Field label width | `80px` |
| Field input width | `424px` |
| Label-input gap | `8px` |
| Field row height | `64px` |
| Field row gap | `0px` (tight stack inside a field block) |
| **Container gap** | `24px` (between non-field blocks: Section, RadioGroup, CheckboxGroup) |

Form Section (info summary block):

| Property | Value |
|----------|------:|
| Padding | `16px` |
| Internal width | `480px` |
| Radius | `radius.lg` (`12px`) |
| Background | `color.fills.f2` |

FormInput (atomic input component):

| Property | Value |
|----------|------:|
| Height | `40px` |
| Outer height (with error space) | `64px` |
| Padding | `12px` horizontal, `10px` vertical |
| Radius | `radius.lg` (`12px`) |

Rules:

- Form width is always inherited from its parent container. Do not hard-code `512px` outside Modal context.
- **Container gap is `24px` between non-field top-level blocks** (`FormSection`, `FormRadioGroup`, `FormCheckboxGroup`). This is the vertical spacing of the Form wrapper.
- `FormField` rows stack tightly with no vertical gap. The `64px` row height includes the input and the error-message reserve space, so no extra margin is needed after a `FormField`.
- When used outside a labeled FormField, FormInput instances have a `12px` vertical gap between them.
- Form Section uses `16px` padding on all sides; internal content must fit within `480px`.
- Preserve label width (`80px`) and input width (`424px`) ratios regardless of field count.

### Structure

```
Form Container (inside Modal Content)
├── FormSection (optional, info summary block)
│   └── Section Content (VERTICAL, padding 16px)
│       ├── Title Row (HORIZONTAL)
│       │   ├── Section title text
│       │   └── InfoIcon (16px, optional)
│       └── Data Rows (HORIZONTAL, multi-column)
├── FormRadioGroup[] (optional)
│   └── Radio Row (HORIZONTAL)
│       ├── Label (80px)
│       └── Options (SelectionControl instances, mode="radio", gap 8px–16px)
├── FormCheckboxGroup[] (optional)
│   └── Checkbox Row (HORIZONTAL)
│       ├── Label (80px)
│       └── Options (SelectionControl instances, mode="checkbox", gap 16px)
├── FormField[] (required)
│   └── Field Row (HORIZONTAL, 64px, items START)
│       ├── Label (80px, 40px high, top-aligned)
│       └── FormInput (424px, 64px)
└── FormFooter (provided by parent Modal, not defined here)
```

**FormSection:**

- Layout: vertical, padding `16px` on all sides.
- Background: `color.fills.f2`.
- Radius: `radius.lg`.
- **Title row**: horizontal, items center-aligned.
  - Title text: `typography.webUI.b2Emphasized`. Color: `color.labels.primary`.
  - InfoIcon: `16px`, from `icon-system.md`. Positioned immediately after the title text with `4px` gap.
- **Data rows**: horizontal, multi-column layout. Each column contains a label + value pair.
  - Label text: `typography.webUI.b2Regular`. Color: `color.labels.tertiary`.
  - Value text: `typography.webUI.b2Regular`. Color: `color.labels.primary`.

**FormRadioGroup:**

- Layout: horizontal, items center-aligned. Full width.
- **Label**: width `80px`. Text: `typography.webUI.b2Regular`. Color: `color.labels.primary`.
- **Options**: horizontal, items center-aligned. Gap between options: `8px`–`16px` depending on density.
- Each option is a **SelectionControl** instance with `mode="radio"` (from the design system) used in mutually exclusive behavior.
  - SelectionControl size: `20px` or `24px` depending on density.
  - Option label: `typography.webUI.b2Regular`. Color: `color.labels.primary`.
  - Gap between circular control and label: `4px`–`8px`.
  - Radio-mode controls use the same circular checkmark visual as checkbox-mode controls. Do not use a dot.

**FormCheckboxGroup:**

- Layout: horizontal, items center-aligned. Full width.
- **Label**: width `80px`. Text: `typography.webUI.b2Regular`. Color: `color.labels.primary`.
- **Options**: horizontal, items center-aligned. Gap between options: `16px`.
- Each option is a **SelectionControl** instance with `mode="checkbox"` (from the design system) used in independent multi-select behavior.
  - SelectionControl size: `20px` or `24px` depending on density.
  - Option label: `typography.webUI.b2Regular`. Color: `color.labels.primary`.
  - Gap between circular control and label: `4px`–`8px`.
  - Checkbox-mode controls use the same circular checkmark visual as radio-mode controls. Do not use a square checkbox.

**FormField:**

- Layout: horizontal, items start-aligned (top). Height `64px`. Full width.
- **Label**: width `80px`, height `40px`. Top-aligned with the input.
  - Text: `typography.webUI.b2Regular`. Color: `color.labels.primary`.
  - If the label text exceeds `80px`, truncate with ellipsis. Do not wrap or widen the label.
- **FormInput**: width `424px`, outer height `64px`.
  - Follow FormInput rules below. Do not invent new input styles inside FormField.

**FormInput:**

- Container: `flex-col`, items start.
- **Input box**: height `40px`, width `100%`.
  - Padding: `12px` horizontal, `10px` vertical.
  - Radius: `radius.lg`.
  - Border: `0.5px solid` at all times. Default color matches the background (`color.fills.f1`); switches to `color.status.danger` in error state.
- **Text container**: flex, items center. Max-height `120px`.
  - Text: `typography.webUI.b2Regular`.
- **Error message** (when `error` is true): below the input box, gap `2px`.
  - Text: `typography.webUI.b2Regular`. Color: `color.status.danger`.
  - Single line preferred; truncate with ellipsis if longer.

### Token Relationship

Use `tokens.json` for color, typography, radius, and effects.

Form-specific metrics (label width, input width, row height, padding) are component-level values from the Figma source. Do not convert them into new spacing tokens unless the design system later defines those tokens.

| Element | Token path | Fallback value |
|---------|-----------|---------------|
| Form Section background | `color.fills.f2` | `rgba(0,0,0,0.05)` |
| Form Section radius | `radius.lg` | `12px` |
| Field label text | `typography.webUI.b2Regular` | — |
| Field label color | `color.labels.primary` | — |
| Input background (empty) | `color.fills.f1` | `rgba(0,0,0,0.03)` |
| Input background (filled/focus/error) | `color.fills.f1` | `rgba(0,0,0,0.03)` |
| Input background (disabled) | `color.fills.f2` | `rgba(0,0,0,0.05)` |
| Input placeholder (empty/focus) | `color.labels.tertiary` | — |
| Input text (filled) | `color.labels.primary` | — |
| Input radius | `radius.lg` | `12px` |
| Input border (default) | `color.fills.f1` | `rgba(0,0,0,0.03)` |
| Input border (error) | `color.status.danger` | `#ff3849` |
| Error text | `color.status.danger` | `#ff3849` |
| Error text style | `typography.webUI.b2Regular` | — |
| Section title text | `typography.webUI.b2Emphasized` | — |

### Form Input States

**Empty (default):**

- Background: `color.fills.f1`.
- Placeholder text: `color.labels.tertiary`.
- Border: `0.5px solid color.fills.f1` (matches background, visually invisible).
- Cursor: default (text cursor on hover).

**Focus:**

- Background: `color.fills.f1`.
- Placeholder text: `color.labels.tertiary`.
- Border: `0.5px solid color.fills.f1`.
- Cursor: text cursor visible.

**Filled:**

- Background: `color.fills.f1`.
- Text: `color.labels.primary`.
- Border: `0.5px solid color.fills.f1`.

**Error:**

- Background: `color.fills.f1`.
- Border: `0.5px solid color.status.danger` (only the border-color changes; width and layout remain stable).
- Text: `color.labels.primary` (if filled) or `color.labels.tertiary` (if placeholder).
- Error message below input: `color.status.danger`, `typography.webUI.b2Regular`.
- Gap between input and error message: `2px`.

**Disabled:**

- Background: `color.fills.f2`.
- Text: `color.fills.f3`.
- Border: `0.5px solid color.fills.f2` (matches disabled background).
- Cursor: `not-allowed`.
- Input is not focusable.

**Loading (form submit):**

- Form transitions to `loading` state internally. Button states are managed by the Button component; Form does not define them.
- Form remains fully visible. Do not replace the form surface with a spinner.
- Input fields remain editable unless explicitly disabled.

### Behavior

**Opening:**

- Form is opened inside a Modal. Follow `references/animation.md` §4.5 Modal pattern.
- Focus moves to the first input field in the form.

**Validation:**

- Trigger on submit, or on blur for real-time validation.
- When a field becomes invalid, switch to error state immediately.
- Focus the first invalid field after failed submission.

**Submit:**

- Triggered by the parent Modal's primary action in the footer.
- Form submits its data and transitions to `loading` state internally. Button loading state is handled by the Button component; Form does not define it.
- On success: close the parent Modal and show a success Toast.
- On failure: keep Modal open, mark invalid fields, focus the first error.

**Cancel / Close:**

- Triggered by the parent Modal's cancel action, Modal Close button, backdrop click, or Escape.
- If the form has unsaved changes, show a confirmation Dialog before closing.
- If no changes, close immediately.

**Scroll handling:**

- When form content exceeds Modal height, scroll only the form content area.
- Title, description, and footer remain fixed.

### Accessibility

- Each `FormField` label must be programmatically associated with its input via `htmlFor` + `id`.
- Error messages must be linked to the input via `aria-describedby`.
- Required fields must have both a visual indicator (`*` or explicit label) and `aria-required="true"`.
- When form validation fails on submit, move focus to the first field in error state.
- Radio-mode selection groups must use `role="radiogroup"` and `aria-label` (or `aria-labelledby` pointing to the group label).
- Trap focus inside the parent Modal while the form is open.
- Respect `prefers-reduced-motion`: skip background color transition, use instant state change.

### Form vs Modal

Form is not a standalone overlay. It is a content layout pattern used inside Modal (or dedicated pages). Modal provides the frame, title, close button, backdrop, and footer. Form provides the field organization, input states, and validation rules.

| | Form | Modal |
|--|------|-------|
| **Type** | Content layout | Overlay container |
| **Owns** | Fields, sections, input states, validation | Frame, backdrop, title, close, footer |
| **Used inside** | Modal, pages | Standalone |
| **Width** | Inherits from parent (`512px` in Modal medium) | `small`/`medium`/`large` |

When in doubt: if the surface needs a title, close button, backdrop, or footer actions, use **Modal** as the container and **Form** as its content.

### Code Guidance

```ts
type FormInputState = "empty" | "focus" | "filled" | "error" | "disabled";

interface FormInputProps {
  value?: string;
  placeholder?: string;
  disabled?: boolean;
  error?: string; // error message; when provided, input is in error state
  onChange?: (value: string) => void;
  onBlur?: () => void;
}

interface FormFieldProps {
  label: string;
  required?: boolean;
  error?: string;
  children: React.ReactNode; // FormInput instance
}

interface FormSectionProps {
  title: string;
  showInfo?: boolean;
  children: React.ReactNode; // data row content
}

interface FormRadioGroupProps {
  label: string;
  options: { value: string; label: string }[];
  value?: string;
  onChange?: (value: string) => void;
}

interface FormCheckboxGroupProps {
  label: string;
  options: { value: string; label: string }[];
  values?: string[];
  onChange?: (value: string, checked: boolean) => void;
}

interface FormProps {
  sections?: FormSectionProps[];
  fields: FormFieldProps[];
  radioGroups?: FormRadioGroupProps[];
  checkboxGroups?: FormCheckboxGroupProps[];
  footer?: React.ReactNode; // provided by parent Modal; Form does not define button content
}
```

Implementation notes:

- Prefer CSS variables generated from `tokens.json` mappings.
- **FormField must compose a FormInput instance via the `children` prop. Do not define new input styles inside FormField.**
- FormInput width should use `100%` inside FormField; the `424px` width is enforced by the parent layout, not the input itself.
- FormInput placeholder color uses `color.labels.tertiary` in both empty and focus states.
- Error border is `0.5px` — ensure the browser can render sub-pixel borders or fall back to `1px`.
- FormSection background must not use a hard-coded hex; map to `color.fills.f2`.

```tsx
// Correct: FormField composes a FormInput instance
<FormField label="邮箱地址" error={emailError}>
  <FormInput
    placeholder="请输入电子邮箱地址，用于接受电子发票"
    value={email}
    onChange={setEmail}
  />
</FormField>
```

- FormField defines where the label sits and how the input is composed; FormInput defines what the input looks like and how it behaves across states.

---
