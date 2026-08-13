# Icon System Stress Test Cases

Use these cases to verify that the AI correctly resolves semantic ambiguity, variant selection, and context-dependent icon mapping.

## Difficulty Levels

- 🟢 **Standard**: Direct semantic match, should be easy.
- 🟡 **Tricky**: Near-synonyms or context-dependent.
- 🔴 **Hard**: Deliberate ambiguity, variant traps, or metaphorical usage.
- ⚫ **Hell**: Missing icon, conflicting rules, or requires judgment call.

---

## 🟡 Tricky Cases

### T1. "Settings" vs "Management"

**Prompt**: "Build a settings page with a user profile section and an admin management section. What icons for each?"

**Expected**:
- User settings → `SettingIcon` (personal preferences)
- Admin management → `ManagementIcon` (system-level admin)

**Why tricky**: Both translate to "设置" in Chinese. The AI must distinguish personal settings from admin management.

### T2. "New" can mean many things

**Prompt**: "A toolbar with three buttons: 'New Chat', 'New Document', 'New Project'. What icon for each?"

**Expected**:
- New Chat → `AddConversationIcon` (chat-specific)
- New Document → `DocumentIcon` or `AddIcon` + document context
- New Project → `AddIcon` or `CreateIcon`

**Why tricky**: All are "new" but belong to different categories.

### T3. "Scan" is overloaded

**Prompt**: "Three features: 'Scan QR Code', 'Scan Math Problem', 'Scan Text (OCR)'. What icon for each?"

**Expected**:
- Scan QR Code → `ScanIcon`
- Scan Math Problem → `ScanMathIcon`
- Scan Text / OCR → `RecognizeIcon`

**Why tricky**: All are "scan" in Chinese (扫描), but have distinct specialized icons.

### T4. "History" vs "List" vs "Catalog"

**Prompt**: "A sidebar has 'Browse History', 'Document List', and 'Resource Catalog'. What icon for each?"

**Expected**:
- Browse History → `HistoryIcon`
- Document List → `ListIcon`
- Resource Catalog → `CatalogIcon`

**Why tricky**: All are "browsing past items" but have different list-visualization semantics.

### T5. "Share" vs "Export" vs "Copy Link"

**Prompt**: "Three actions: 'Share to Social Media', 'Export as File', 'Copy Link'. What icon for each?"

**Expected**:
- Share to Social Media → `ShareIcon`
- Export as File → `OutputIcon` or `DownloadIcon`
- Copy Link → `CopyIcon` or `LinkIcon`

**Why tricky**: Users often conflate "share" and "export". The AI must respect `ShareIcon.avoid_for: ["export to file"]`.

---

## 🔴 Hard Cases

### H1. Variant Trap: Like vs Like_b

**Prompt**: "A feedback widget with thumbs-up and thumbs-down. Which variant should I use, `LikeIcon` or `Like_bIcon`?"

**Expected**:
- Default: `LikeIcon` (non-suffixed is the default)
- Only use `Like_bIcon` if the product spec or Figma explicitly calls for the filled/thicker variant.

**Why hard**: The difference between `Like` and `Like_b` is visual/subtle. The AI must default to non-suffixed unless context demands it.

### H2. Variant Trap: Send_a vs Send_b

**Prompt**: "A send button in the chat input. Should I use `Send_aIcon` or `Send_bIcon`?"

**Expected**:
- Default: `Send_aIcon` (primary send)
- `Send_bIcon` only if there's a secondary send style (e.g., different context or state).

**Why hard**: Both are "send". The AI must know the `_b` suffix rule.

### H3. Metaphor: "AI is thinking"

**Prompt**: "Show a status that 'AI is thinking / processing'. What icon?"

**Expected**:
- `LoadingRightIcon` (process in progress)
- NOT `RobotIcon` (that's a brand/product icon, not a state)
- NOT `KimiPlusIcon` (brand, not state)

**Why hard**: "AI thinking" could trigger brand icons (`Robot`, `KimiPlus`, `Prism`) instead of status icons.

### H4. Metaphor: "Deep Research"

**Prompt**: "A button to enter 'Deep Research Mode'. What icon?"

**Expected candidates** (ranked by fit):
1. `ProSearchIcon` — literally "pro search"
2. `MicroscopeIcon` — metaphor for deep inspection
3. `KnowledgeIcon` — research knowledge base

**Why hard**: No single "research" icon exists. The AI must choose the closest semantic match and explain the trade-off.

### H5. Metaphor: "Generate Content"

**Prompt**: "A creation hub with four buttons: 'Generate Image', 'Generate Audio', 'Generate Text', 'Generate Video'. What icon for each?"

**Expected**:
- Generate Image → `ImageCreateIcon` or `ImageGenerateIcon`
- Generate Audio → `SoundGenerateIcon`
- Generate Text → `WriteIcon`
- Generate Video → ??? (no dedicated video-gen icon; closest is `VideoIcon` or `ImageCreateIcon`)

**Why hard**: One of four has no direct match. The AI should note the gap instead of inventing one.

### H6. Reverse action pairs

**Prompt**: "A toggle pair: 'Browse' vs 'Unbrowse', 'Pin' vs 'UnpinFromTop', 'Like' vs 'Dislike'. Match the correct icon pairs."

**Expected**:
- Browse / Unbrowse → `BrowseIcon` + `UnbrowseIcon` ✅
- Pin / Unpin → `PinToTopIcon` + `UnpinFromTopIcon` ✅
- Like / Dislike → `LikeIcon` + `DislikeIcon` ✅

**Why hard**: Tests whether the AI recognizes explicit inverse-icon pairs vs defaulting to generic toggles.

### H7. Directional maze

**Prompt**: "A pagination UI: 'First Page', 'Previous Page', 'Next Page', 'Last Page'. What icons?"

**Expected**:
- First Page → ??? (no explicit "first" icon; closest is `PreviousIcon` or a custom double-arrow)
- Previous Page → `PreviousIcon`
- Next Page → `NextIcon`
- Last Page → ??? (no explicit "last" icon)

**Why hard**: The icon set has `Previous`/`Next` but no `First`/`Last`. The AI should note the missing icons and suggest `Previous`/`Next` as partial coverage.

### H8. "Enter" vs "Next" vs "MoveForward"

**Prompt**: "Three buttons in a wizard: 'Enter Step 2', 'Next Step', 'Skip Forward'. What icon for each?"

**Expected**:
- Enter Step 2 → `EnterIcon` or `Enter_rIcon`
- Next Step → `NextIcon`
- Skip Forward → `MoveForwardIcon`

**Why hard**: All imply forward progression. The AI must distinguish "enter/into" from "next/adjacent" from "skip/ahead".

---

## ⚫ Hell Cases

### X1. The "设置" Trap

**Prompt**: "Build a page with these sections, each needing an icon: 'Account Settings', 'Notification Settings', 'System Management', 'Plugin Management', 'Theme Settings'."

**Expected**:
- Account Settings → `SettingIcon` or `ProfileIcon`
- Notification Settings → `SettingIcon` or `NotificationIcon`
- System Management → `ManagementIcon`
- Plugin Management → `ManagementIcon` or `ConnectorsIcon`
- Theme Settings → `SettingIcon` or `LightModeIcon`/`DarkModeIcon`

**Why hell**: 5 items, 3 map to "settings/management". The AI must avoid using the same icon for all 5 while staying within the design system.

### X2. The "Create" Ambiguity

**Prompt**: "A creation menu with: 'Create Document', 'Create Image', 'Create Task', 'Create Conversation', 'Create Spreadsheet'. What icon for each?"

**Expected**:
- Create Document → `DocumentIcon` (or `AddIcon` + label)
- Create Image → `ImageCreateIcon`
- Create Task → `TaskIcon` or `TodoIcon`
- Create Conversation → `AddConversationIcon`
- Create Spreadsheet → `ExcelIcon`

**Why hell**: "Create" is the action, but each target has its own noun-icon. The AI must pair the action with the object icon, not just use `CreateIcon` for everything.

### X3. Missing Icon — "Print"

**Prompt**: "I need a 'Print' button. What's the icon?"

**Expected**:
- No `PrintIcon` exists in the library.
- AI should say: "No PrintIcon in `manifest.json`. Options: (1) request adding one, (2) use `OutputIcon` as closest semantic fallback, (3) use project-specific icon."

**Why hell**: Tests whether the AI invents an icon or silently substitutes vs properly reporting a gap.

### X4. Missing Icon — "Calendar / Date"

**Prompt**: "A date picker input needs a calendar icon. What should I use?"

**Expected**:
- No calendar icon exists.
- AI should note the gap and suggest either adding one or using a text-based fallback.

**Why hell**: Calendar is a very common UI element. The absence tests the AI's gap-handling rule from `SKILL.md`.

### X5. The "Analyze" Multiverse

**Prompt**: "Three analysis features: 'Data Analysis', 'Image Analysis', 'Code Analysis'. What icon for each?"

**Expected**:
- Data Analysis → `DiagramIcon`, `TabularIcon`, or `DataIcon`
- Image Analysis → `ImageIcon` or `MagnifyIcon`
- Code Analysis → `CodeIcon`

**Why hell**: "Analysis" is abstract. The AI must resolve it through the object being analyzed, not search for a generic "analysis" icon (which doesn't exist).

### X7. Compound Action: "Upload to WeChat"

**Prompt**: "An 'Upload to WeChat' button. What icon?"

**Expected**:
- `UploadWechatIcon` — it's a specific icon for this exact action.
- NOT generic `UploadIcon`.

**Why hell**: Tests whether the AI checks for highly specific compound icons before falling back to generic ones.

### X8. State + Action Combo

**Prompt**: "A button that changes based on state: default state is 'Pin this message', already-pinned state is 'Unpin from top'. Write the code with correct icons for both states."

**Expected**:
- Default → `PinToTopIcon`
- Pinned → `UnpinFromTopIcon`
- NOT the same icon for both states.

**Why hell**: Tests whether the AI understands stateful icon pairs and can generate conditional code.

---

## Test Runner Template

Copy this into your AI session:

```
我正在测试 kimi-design-skill 的图标语义索引。请回答以下问题。

对每个问题，你必须说明：
1. 你读取了哪个索引文件（manifest.json 或 categories/*.json）
2. 你最终选择的图标名称
3. 选择理由（引用 use_for / avoid_for / 变体规则）
4. 如果有多个候选，说明你为什么排除了其他选项

---

Q1. [选一个 Tricky Case，如 T3 Scan 三选一]
Q2. [选一个 Hard Case，如 H4 Deep Research]
Q3. [选一个 Hell Case，如 X3 Print 缺失]
Q4. [选一个 Variant Trap，如 H1 Like vs Like_b]
Q5. [选一个反向对，如 H6 Browse/Unbrowse]
Q6. [自定义一个你的业务场景]
```

---

## Scoring Rubric

| 分值 | 表现 |
|------|------|
| 5/5 | 正确选择图标，引用了 `avoid_for` 排除错误选项，正确处理缺失图标（报告 gap），变体选择符合规则 |
| 4/5 | 正确选择图标，能说出理由，但未引用具体的 `avoid_for` 或变体规则 |
| 3/5 | 选择了可用但不最优的图标（如用 `SearchIcon` 代替 `MagnifyIcon`） |
| 2/5 | 选择了明显错误的图标（如用 `UploadIcon` 表示下载） |
| 1/5 | 引用了外部图标库或发明了不存在的图标名 |
| 0/5 | 完全没读取索引，凭文件名猜测 |

**Pass threshold**: 平均每题 ≥ 4/5。
