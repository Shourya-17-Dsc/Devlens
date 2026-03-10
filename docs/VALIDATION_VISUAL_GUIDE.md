# Visual Guide: Username Validation Feature

## Home Page - Search Interface

### Scenario 1: Invalid Format (Spaces)
```
┌─ DevLens ────────────────────────────────────┐
│                                              │
│  🧠 Skill Intelligence                      │
│  Analyze GitHub profiles and discover       │
│  developer skills                           │
│                                              │
│  GitHub Username                             │
│  ┌──────────────────────────────────────┐  │
│  │ john doe                    Validating   │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │ ⚠️ Username can only contain         │  │
│  │    letters, numbers, and hyphens    │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  [Analyze Profile →] (disabled/grayed)      │
│                                              │
└──────────────────────────────────────────────┘
```

### Scenario 2: Checking if Username Exists
```
┌─ DevLens ────────────────────────────────────┐
│                                              │
│  🧠 Skill Intelligence                      │
│                                              │
│  GitHub Username                             │
│  ┌──────────────────────────────────────┐  │
│  │ torvalds                             │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  [⏳ Validating...] (loading spinner)       │
│                                              │
└──────────────────────────────────────────────┘
        ↓ (checking with GitHub API)
```

### Scenario 3: Invalid Username Found
```
┌─ DevLens ────────────────────────────────────┐
│                                              │
│  🧠 Skill Intelligence                      │
│                                              │
│  GitHub Username                             │
│  ┌──────────────────────────────────────┐  │
│  │ xyz-invalid-user-abc                 │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │ ❌ Invalid GitHub username           │  │
│  │    - user not found                  │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  [Analyze Profile →] (disabled/grayed)      │
│                                              │
└──────────────────────────────────────────────┘
```

### Scenario 4: Valid Username - Ready to Analyze
```
┌─ DevLens ────────────────────────────────────┐
│                                              │
│  🧠 Skill Intelligence                      │
│                                              │
│  GitHub Username                             │
│  ┌──────────────────────────────────────┐  │
│  │ octocat                              │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  [✅ Analyze Profile →] (enabled/blue)      │
│                                              │
│  What you'll see:                            │
│  ✨ ML-powered skill score (0-10)           │
│  📊 Language breakdown & expertise          │
│  💪 Technical strengths analysis            │
│  📈 Code complexity metrics                 │
│  🔄 Activity level classification           │
│                                              │
└──────────────────────────────────────────────┘
        ↓ (navigates to profile)
```

## Profile Page - Error Display

### Scenario: User Not Found (Invalid Username)
```
┌─────────────────────────────────────────────┐
│ GitHub Skill Analysis                       │
│ ← Back                                      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│                     ⚠️                       │
│                                              │
│  Invalid GitHub Username                    │
│                                              │
│  ❌ Invalid GitHub Username:               │
│  'invalid-user' does not exist on GitHub.   │
│  Please check the username and try again.   │
│                                              │
│  [← Try Another Username]  [Go Back]        │
│                                              │
└─────────────────────────────────────────────┘
```

### Scenario: Loading Profile
```
┌─────────────────────────────────────────────┐
│ GitHub Skill Analysis                       │
│ ← Back                                      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│           ⟳ (spinning loader)               │
│                                              │
│      Analyzing profile...                   │
│                                              │
│      (fetching from GitHub API)             │
│      (computing ML predictions)             │
└─────────────────────────────────────────────┘

           ~3 seconds typical
```

### Scenario: Valid Profile Found
```
┌─────────────────────────────────────────────┐
│ GitHub Skill Analysis                       │
│ ← Back                                      │
│ octocat                                     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Skill Score                              75│
│  ML-powered rating from 0-100 based...      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Language Breakdown              [CHART]    │
│                                              │
│  JavaScript    350 repos                    │
│  Python        145 repos                    │
│  TypeScript     89 repos                    │
└─────────────────────────────────────────────┘

┌──────────────────┬──────────────────┐
│  💪 Strengths   │  ⚡ Areas to Grow│
│                  │                  │
│ ✅ Good Doc...  │ ❌ Low Commit... │
│ ✅ Polyglot...  │ ❌ No Tests...   │
└──────────────────┴──────────────────┘

[More sections below...]
```

## Validation Decision Tree

```
User enters username
        ↓
    Is it empty?
    /        \
  YES        NO
   |          |
[Error:      Is length ≤ 39?
"Please      /            \
enter       YES           NO
username"]   |             |
            [Error:    "Username
    Does it start/   cannot
    end with dash?   exceed 39
    /          \     characters"]
  YES         NO
   |           |
[Error:   [Is it valid
"Cannot    characters?
start/end  /         \
with dash"] YES       NO
   |        |         |
   |    [API       [Error:
   |    Check]   "Only letters,
   └─→  /    \   numbers, and
        /      \  hyphens"]
      Exists  Not Found
       /          \
      ✅          ❌
    Redirect   [Show Error:
    to      "Invalid username
    Profile -user not found"]
```

## State Transitions

```
IDLE
 ├─ User types → EDITING
 │   └─ Format invalid → Show error
 │   └─ Format valid → READY
 │
READY
 ├─ User clicks "Analyze" → VALIDATING
 │   └─ Calling GitHub API...
 │
VALIDATING
 ├─ API returns 200 → VALID (redirect to profile)
 ├─ API returns 404 → INVALID (show error message)
 └─ API error → API_ERROR (show technical error)
 │
PROFILE_LOADING
 ├─ Data loaded → PROFILE_READY (display dashboard)
 └─ 404 error → PROFILE_NOT_FOUND (show error)
```

## Color Scheme

### Input Field States
- **Default**: Gray border (#D1D5DB)
- **Focused**: Blue border (#3B82F6)
- **Error**: Red background (#FEF2F2)
- **Disabled**: Gray background (#F3F4F6)

### Error Messages
- **Format Error**: Red text on red background (#FEE2E2 bg, #991B1B text)
- **API Error**: Red border, red icon
- **Loading state**: Blue spinner

### Buttons
- **Enabled**: Blue (#2563EB)
- **Disabled**: Gray (#9CA3AF)
- **Hover**: Darker blue (#1D4ED8)

## Animation Details

### Loading Spinner
```css
Animation: rotate 1s linear infinite;
Size: 16px diameter
Color: White
Position: Button left side
```

### Validation Check Animation
```
When user types → Brief pause (500ms)
Format check → Instant feedback
If format valid → Button highlights
If button clicked → Spinner starts
```

---

**Visual Guide Version**: 1.0  
**Last Updated**: March 10, 2026  
**Status**: ✅ Complete and Tested
