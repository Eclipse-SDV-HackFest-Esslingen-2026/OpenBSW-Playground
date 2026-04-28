---
description: "OpenBSW C++ coding conventions and guidelines. Use when writing, reviewing, or refactoring C++ code in the OpenBSW codebase. Covers naming, const correctness, initialization, disallowed features, enumerations, classes, functions, namespaces, formatting, and safe coding practices."
applyTo: "**/*.{cpp,h,hpp,cc,hh,hxx}"
---

# OpenBSW C++ Coding Guidelines

Full guidelines live in `openbsw/doc/dev/guidelines/`. When in doubt, read the source:
- Conventions: `openbsw/doc/dev/guidelines/conventions/`
- Formatting:  `openbsw/doc/dev/guidelines/formatting/`
- Practices:   `openbsw/doc/dev/guidelines/practices.rst`

---

## Naming

> Full rules: `conventions/naming.rst`

- **Types** (classes, structs, aliases, enums): `UpperCamelCase` — `TcpConnection`, `ReturnCode`
- **Variables and function parameters**: `lowerCamelCase` — `ipAddress`, `bufferSize`
- **Class member variables**: `_lowerCamelCase` (leading underscore) — `_addr`, `_port`
- **Static-storage constants** (`static const`, `constexpr`, global `const`): `ALL_CAPS_WITH_UNDERSCORES`
- **Local non-static constants**: `lowerCamelCase` (same as variables)
- **Functions and methods**: `lowerCamelCase` — `getDigital()`, `establishConnection()`
- **Namespaces**: `lowerCamelCase` — `namespace tcpip {}`
- No Hungarian notation. No type prefixes on variables.
- Names must be in English and intention-revealing (CPP-002).
- Always qualify global namespaces with `::`: `::common::io::getDigital()` not `common::io::getDigital()`

---

## Const Correctness (east-const)

> Full rules: `conventions/constants.rst`

- `const` goes **to the right of the type** it modifies (east-const style):
  ```cpp
  int const x = 42;       // good
  const int x = 42;       // bad
  char const* ptr;        // pointer to const char — good
  ```
- Make objects `const` by default; remove `const` only when mutation is required.
- Mark member functions `const` unless they change logical state.
- `const` on value parameters: omit from **declarations**, keep in **definitions**:
  ```cpp
  void func(size_t len);              // declaration — no const
  void func(size_t const len) { }     // definition — const OK here
  ```

---

## Initialization

> Full rules: `conventions/initialization.rst`

- Prefer **direct initialization** for built-in types:
  ```cpp
  uint16_t port(8080U);    // good
  uint16_t port = 8080U;   // avoid (copy initialization)
  ```
- Use **direct-list-initialization** for aggregates and structs:
  ```cpp
  xyz point{x, y, z};
  ```
- Use **non-static data member initializers (NSDMI)** in class definitions:
  ```cpp
  struct Foo { int count{0}; };
  ```
- Constructor bodies must be **empty** — all initialization goes in the member initializer list:
  ```cpp
  TcpConnection::TcpConnection(Ip addr, uint16_t port)
  : _addr(addr)
  , _port(port)
  {}   // body is empty
  ```

---

## Disallowed Features

> Full rules: `conventions/disallowed.rst`

| Feature | Status | Alternative |
|---------|--------|-------------|
| `new` / `delete` | ❌ Forbidden | Static allocation; `placement new` where needed |
| RTTI (`dynamic_cast`, `typeid`) | ❌ Forbidden | Disabled by compiler flags |
| Exceptions (`throw`, `try`/`catch`) | ❌ Forbidden | Return codes / `ReturnCode` enums |
| Variable-length arrays (VLA) | ❌ Forbidden | Fixed-size arrays; `etl` containers |
| `0` / `NULL` as null pointer | ❌ Forbidden | Use `nullptr` |
| Unscoped enums (`enum Foo {}`) | ❌ Forbidden | `enum class Foo : uint8_t {}` |

---

## Enumerations

> Full rules: `conventions/enumerations.rst`

Always use **scoped enumerations** with an **explicit underlying type**:
```cpp
enum class ReturnCode : uint8_t   // good
{
    OK,
    TIMEOUT,
    ERROR,
};

enum Colors { RED, GREEN };       // bad — unscoped, no explicit type
```

---

## Classes

> Full rules: `conventions/classes.rst`

- Constructor bodies must be empty; use member initializer lists for all setup.
- Fallible initialization → separate `init()` method returning a `ReturnCode`.
- Member variable prefix: `_name` — `_addr`, `_port`, `_buffer`.
- Interfaces: `I`-prefixed name (`IExample`), dedicated header `IExample.h`,
  destructor `protected: ~IExample() = default;`.
- Static interfaces with C++20 concept checks preferred over pure virtual for
  performance-critical paths.

---

## Functions

> Full rules: `conventions/functions.rst`

- One function = one logical operation.
- If a function does not fit on a screen, it is too long — break it up.
- Cheap-to-copy types (≤2–3 words): pass **by value**. Others: pass **by `const` reference**.
- If a function can be evaluated at compile time, declare it `constexpr`.
- Use `[[nodiscard]]` when the return value must not be silently discarded.

---

## Interfaces (Low-Level / BSP)

> Full rules: `conventions/interfaces.rst`

- Prefer **static interfaces with C++20 concept checks** over virtual dispatch for
  performance-critical code.
- If using pure virtual: `protected: ~IInterface() = default;`
- Interface header: `include/bsp/<module>/IExample.h`
- No implementation details in interface headers.
- Isolate platform-specific configuration in separate files, not in the interface.

---

## Statements & Expressions

> Full rules: `conventions/statements.rst`

- No `true`/`false` in comparisons: `if (isGood)` not `if (true == isGood)`
- No trivial if-else around return:
  ```cpp
  return isGood;              // good
  if (isGood) return true;    // bad
  else return false;
  ```
- No magic constants — name them with `constexpr`:
  ```cpp
  constexpr int firstMonth = 1;                  // good
  for (int m = 1; m <= 12; ++m) { ... }         // bad
  ```
- Use `nullptr`, never `0` or `NULL` for pointers.

---

## Comments

> Full rules: `conventions/comments.rst`

- **Minimize comments** — if code needs explaining, rewrite the code instead.
- Describe **what** and **why**, never **how** at micro level.
- Write in English prose with correct spelling, grammar, and punctuation.
- `// clang-format off` / `// clang-format on` to protect manually formatted tables.

---

## Namespaces

> Full rules: `conventions/namespaces.rst`

- Always qualify with `::` from global scope: `::etl::span<uint8_t>`, `::os::Task`
- Place helper functions in the same namespace as their supporting class.
- No `using namespace` in header files.

---

## Formatting

> Full rules: `formatting/for_c++/formatting.rst` — enforced by clang-format

- 4-space indentation; no tabs.
- Namespaces: not indented. Preprocessor directives: not indented.
- `// clang-format off` / `// clang-format on` to opt out a block.
- Apply formatter: `clang-format -style=file -i <file>`
- CI enforces clang-format on every changed file — do not skip it.

---

## Compiler Warnings & Static Analysis

> Full rules: `practices.rst`

- All warnings are **errors**: `-Wall -Werror -Wvla -Woverloaded-virtual`
- Fix warnings in third-party code too; do not suppress without justification.
- clang-tidy runs on every PR (changed-scope) and every push to `main` (full scan).
  Config: `.clang-tidy` in repo root. CI script: `.ci/clang-tidy.py`
- Run locally on a single file:
  ```bash
  clang-tidy-17 -p <path_to_compile_commands_dir> <source_file>
  ```
- Run via the CI script:
  ```bash
  python3 .ci/clang-tidy.py --build_directory <build_dir> --output_file <findings_file>
  ```

---

## Pre-commit Checklist

- [ ] No `new`/`delete`, no RTTI, no exceptions, no VLAs
- [ ] All enums are scoped (`enum class`) with explicit underlying type
- [ ] `const`-correct throughout; east-const style
- [ ] Constructor body is empty; member initializer list used
- [ ] No magic constants — named `constexpr`
- [ ] `nullptr` used; never `0` or `NULL` for pointers
- [ ] Naming: types `UpperCamelCase`, vars `lowerCamelCase`, members `_prefixed`
- [ ] No compiler warnings (`-Werror` will catch them anyway)
- [ ] `clang-format -style=file -i` applied to all changed files
