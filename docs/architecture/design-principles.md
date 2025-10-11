# Design Principles

Core design principles guiding Markdown Reallocator.

## Principles

### 1. Local-First

All operations run locally without cloud dependencies.

**Benefits**:
- No API costs
- Data privacy
- Offline capability

### 2. Modular Design

Each component is independent and reusable.

**Benefits**:
- Use only what you need
- Easy testing
- Clear separation of concerns

### 3. Resource-Efficient

Designed for consumer hardware (2GB GPU).

**Strategies**:
- Automatic model unloading
- Configurable batch sizes
- Caching to reduce computation

### 4. Type-Safe

Full type hints and mypy validation.

**Benefits**:
- Fewer runtime errors
- Better IDE support
- Self-documenting code

### 5. Well-Tested

93%+ code coverage with unit, integration, and smoke tests.

**Benefits**:
- Reliable behavior
- Safe refactoring
- Regression prevention
