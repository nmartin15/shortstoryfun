# Security Documentation

This document describes the security measures implemented in the Short Story Pipeline application and provides guidance for secure deployment and usage.

## Table of Contents

- [Security Features](#security-features)
- [Input Sanitization](#input-sanitization)
- [XSS Prevention](#xss-prevention)
- [Model Security](#model-security)
- [File System Security](#file-system-security)
- [API Security](#api-security)
- [CDN and External Resources](#cdn-and-external-resources)
- [Best Practices](#best-practices)
- [Security Updates](#security-updates)

## Security Features

The application implements multiple layers of security to protect against common vulnerabilities:

### Defense in Depth

- **Input Validation**: All user inputs are validated at the API layer
- **Input Sanitization**: User data is sanitized before use in file operations and UI rendering
- **Output Encoding**: All user-controlled data is properly escaped when displayed
- **Model Validation**: LLM model names are validated against current API availability
- **Rate Limiting**: API endpoints are rate-limited to prevent abuse

## Input Sanitization

### Filename Sanitization

The `sanitize_filename()` function in `src/shortstory/exports.py` protects against:

1. **Path Traversal Attacks**
   - Removes `..` sequences
   - Removes path separators (`/`, `\`)
   - Prevents directory traversal outside intended paths

2. **Command Injection**
   - Removes shell metacharacters: `|`, `&`, `;`, `` ` ``, `$`
   - Prevents command execution if filenames are used in shell commands

3. **OS-Specific Issues**
   - Removes Windows forbidden characters: `:`, `*`, `?`, `<`, `>`, `"`
   - Ensures cross-platform compatibility

4. **XSS in Download Attributes**
   - Removes script tags: `<script>...</script>`
   - Removes JavaScript event handlers: `onclick=`, `onerror=`, etc.
   - Removes `javascript:` protocol handlers
   - Prevents XSS if filenames are reflected in HTML

### Implementation Details

The `sanitize_filename()` function uses pre-compiled regex patterns for optimal performance, especially under high load. All regex patterns are compiled once at module load time to avoid recompilation overhead on each function call.

```python
def sanitize_filename(title: str, story_id: str, max_length: int = 50) -> str:
    """
    Sanitizes filenames by:
    1. Removing path traversal sequences (.., /, \)
    2. Removing dangerous characters (shell metacharacters, OS-forbidden chars)
    3. Removing XSS patterns (script tags, event handlers, javascript: protocol)
    4. Normalizing whitespace to underscores
    5. Removing any remaining non-alphanumeric characters (except _ and -)
    6. Truncating to max_length
    7. Providing safe fallback if result is empty
    
    Performance: Uses pre-compiled regex patterns for efficient processing.
    """
```

**Allowed Characters**: Only alphanumeric characters, underscores (`_`), and hyphens (`-`) are allowed in sanitized filenames.

**Fallback**: If sanitization results in an empty string, a safe fallback is generated using the story ID.

**Performance Optimization**: The function uses pre-compiled regex patterns that are created once at module load time, significantly improving performance when processing many filenames. This is especially important for export operations that may handle multiple files concurrently.

## XSS Prevention

### Frontend Sanitization

All user-controlled data displayed in the UI is sanitized using the `escapeHtml()` function:

```javascript
function escapeHtml(text) {
    // Uses DOM textContent to safely escape HTML entities
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}
```

### Protected Functions

- `loadStoryBrowser()`: Sanitizes story titles, genres, premises, word counts, and IDs
- `displayValidationResults()`: Sanitizes scores, word counts, cliché lists, and suggestions
- `loadRevisionHistory()`: Sanitizes version numbers, timestamps, and word counts

### Best Practices

1. **Never use `innerHTML` with unsanitized data**
2. **Always use `escapeHtml()` for user-controlled data**
3. **Use `textContent` when possible** (for simple text display)
4. **Validate data structure** before accessing nested properties

## Model Security

### Dynamic Model Validation

The LLM client fetches available models dynamically from the Google Gemini API:

```python
# In LLMClient.__init__()
raw_available_models = list(self._genai.list_models())
self.available_models = [m.name.replace("models/", "") for m in raw_available_models]
```

**Benefits**:
- Prevents using deprecated models with known vulnerabilities
- Automatically supports new secure models without code changes
- Reduces risk of using insecure model versions

### Fallback Protection

If dynamic fetching fails, a fallback list is used with security warnings:

```python
except Exception as e:
    logger.error(
        "Failed to fetch available models dynamically, using fallback list (security risk): {e}",
        exc_info=True
    )
    self.available_models = FALLBACK_ALLOWED_MODELS.copy()
```

**Security Note**: The fallback list should be regularly updated to remove deprecated models.

### Model Name Validation

All model names are validated before use:

```python
def _validate_model_name(model_name: str, available_models: List[str]) -> str:
    # Validates against dynamically fetched list
    # Raises ValueError if model is not available
```

## File System Security

### Export Functions

All export functions (`export_pdf`, `export_txt`, `export_markdown`, etc.) use `sanitize_filename()` to ensure safe filenames:

1. **PDF/TXT Exports**: Filenames sanitized before `send_file()` call
2. **Markdown Exports**: Filenames sanitized in `Content-Disposition` header
3. **DOCX/EPUB Exports**: Filenames sanitized before file creation

### Story ID Sanitization

Story IDs are also sanitized when used in filenames. All export functions use the same pre-compiled regex patterns for consistent and efficient sanitization:

```python
# Story ID is sanitized in fallback generation and all export functions
# Uses pre-compiled _NON_ALPHANUMERIC_PATTERN for performance
safe_id = _NON_ALPHANUMERIC_PATTERN.sub('', story_id)[:8]
```

**Performance Note**: All sanitization operations use pre-compiled regex patterns that are created once at module load time, ensuring optimal performance even under high load with many concurrent export operations.

## API Security

### Input Validation

- All API endpoints validate input data types and formats
- Story IDs are validated before use in database queries
- Genre names are validated against allowed list
- Word counts are validated against min/max limits

### Error Handling

- Structured error responses prevent information leakage
- Generic error messages for users, detailed logs for debugging
- No stack traces exposed to clients

### Rate Limiting

- API endpoints are rate-limited using Flask-Limiter
- Prevents abuse and ensures fair resource usage
- Configurable limits per endpoint

## CDN and External Resources

### Current CDN Resources

#### 1. Tailwind CSS (cdn.tailwindcss.com)
- **Status**: Used for development
- **Security**: No SRI support (dynamic content)
- **Recommendation**: Self-host compiled Tailwind CSS for production

#### 2. Google Fonts (fonts.googleapis.com)
- **Status**: Active
- **Security**: HTTPS only, no SRI support
- **Recommendation**: Consider self-hosting for full control

#### 3. GSAP Animation Library (cdn.jsdelivr.net)
- **Version**: 3.12.5 (pinned)
- **Status**: CDN with placeholder SRI hash
- **Security**: SRI hash should be generated and added
- **Recommendation**: Self-host in `static/js/gsap.min.js` (preferred)

#### 4. Lucide Icons (unpkg.com)
- **Version**: 0.263.1 (pinned)
- **Status**: CDN with placeholder SRI hash
- **Security**: SRI hash should be generated and added
- **Recommendation**: Self-host in `static/js/lucide.min.js` (preferred)

### Subresource Integrity (SRI)

SRI allows browsers to verify that resources haven't been tampered with. Always use SRI hashes for CDN resources when possible.

#### Generating SRI Hashes

```bash
# Method 1: From a local file
openssl dgst -sha384 -binary <file> | openssl base64 -A

# Method 2: From a URL (download first)
curl -s https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js | \
  openssl dgst -sha384 -binary | openssl base64 -A
```

#### Using SRI in HTML

```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js" 
        integrity="sha384-GENERATED_HASH_HERE" 
        crossorigin="anonymous" 
        defer></script>
```

### Self-Hosting Resources

**Benefits:**
- Full control over resource versions
- No dependency on external CDN availability
- Better performance (no external DNS lookup)
- Full SRI support
- Offline capability

**Implementation:**

1. Download the resource:
   ```bash
   curl -o static/js/gsap.min.js https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js
   curl -o static/js/lucide.min.js https://unpkg.com/lucide@0.263.1
   ```

2. Generate SRI hash:
   ```bash
   openssl dgst -sha384 -binary static/js/gsap.min.js | openssl base64 -A
   ```

3. Update HTML to use local file:
   ```html
   <script src="{{ url_for('static', filename='js/gsap.min.js') }}" 
           integrity="sha384-GENERATED_HASH_HERE" 
           crossorigin="anonymous" 
           defer></script>
   ```

### Recommended Production Setup

#### Option 1: Self-Host All Resources (Recommended)

1. **Tailwind CSS**: Compile and self-host
   ```bash
   npx tailwindcss -i ./src/input.css -o ./static/css/tailwind-compiled.css --minify
   ```

2. **GSAP**: Download and self-host
   ```bash
   curl -o static/js/gsap.min.js https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js
   ```

3. **Lucide Icons**: Download and self-host
   ```bash
   curl -o static/js/lucide.min.js https://unpkg.com/lucide@0.263.1
   ```

4. **Google Fonts**: Self-host (optional but recommended)
   - Download font files from Google Fonts
   - Place in `static/fonts/`
   - Update CSS to reference local files

#### Option 2: CDN with SRI (Acceptable)

1. Generate SRI hashes for all CDN resources
2. Update HTML with actual SRI hashes (replace placeholders)
3. Pin all versions (no `@latest`)
4. Monitor for security updates

### Version Pinning

**Always pin versions** to avoid unexpected breaking changes:
- ✅ Good: `gsap@3.12.5`
- ❌ Bad: `gsap@latest` or `gsap@3`

### Font Preloading

Critical fonts are preloaded to improve performance:

```html
<link rel="preload" href="https://fonts.gstatic.com/s/inter/v13/..." 
      as="font" 
      type="font/woff2" 
      crossorigin="anonymous">
```

### Updating Resources

When updating a CDN resource:

1. **Download new version**:
   ```bash
   curl -o static/js/gsap.min.js https://cdn.jsdelivr.net/npm/gsap@NEW_VERSION/dist/gsap.min.js
   ```

2. **Generate new SRI hash**:
   ```bash
   openssl dgst -sha384 -binary static/js/gsap.min.js | openssl base64 -A
   ```

3. **Update HTML** with new version and hash

4. **Test thoroughly** to ensure compatibility

## Best Practices

### For Developers

1. **Always sanitize user input** before use in file operations
2. **Always escape user data** before rendering in HTML
3. **Validate model names** against current API availability
4. **Use parameterized queries** for database operations (already implemented)
5. **Log security events** (e.g., fallback model list usage)
6. **Keep dependencies updated** and review security advisories
7. **Review and test** sanitization functions when adding new features

### For Deployment

1. **Set secure environment variables**:
   ```bash
   export GOOGLE_API_KEY=your_secure_key
   export FLASK_ENV=production
   export SECRET_KEY=your_secret_key
   ```

2. **Use HTTPS** in production (configure reverse proxy)
3. **Enable security headers** (CSP, X-Frame-Options, etc.)
4. **Regular security updates**:
   - Update Python dependencies: `pip install --upgrade -r requirements.txt`
   - Review and update fallback model list
   - Update pinned CDN resource versions

4. **Monitor security logs** for:
   - Failed model validation attempts
   - Fallback model list usage
   - Rate limit violations
   - Unusual API usage patterns

### For Users

1. **Use strong API keys** and rotate them regularly
2. **Don't share API keys** or commit them to version control
3. **Review generated content** before publishing
4. **Report security issues** responsibly (see below)

## Security Updates

### Regular Maintenance

1. **Weekly**: Review dependency security advisories
2. **Monthly**: Update fallback model list if new models are released
3. **Quarterly**: Review and update security documentation
4. **As needed**: Update when security vulnerabilities are discovered

### Dependency Updates

Check for security vulnerabilities:

```bash
# Using pip-audit (if installed)
pip-audit

# Using safety (if installed)
safety check

# Manual review
pip list --outdated
```

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT** open a public GitHub issue
2. **Do NOT** discuss the vulnerability publicly
3. **Email** the maintainers directly with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

We will:
- Acknowledge receipt within 48 hours
- Investigate and confirm the vulnerability
- Develop and test a fix
- Release a security update
- Credit you (if desired) in the security advisory

## Security Checklist

Before deploying to production:

- [ ] All environment variables are set securely
- [ ] HTTPS is enabled
- [ ] Security headers are configured
- [ ] Rate limiting is enabled and configured
- [ ] Dependencies are up to date
- [ ] Fallback model list is current
- [ ] CDN resources are pinned to specific versions (no `@latest`)
- [ ] All CDN resources have SRI hashes (or are self-hosted)
- [ ] Critical resources are self-hosted
- [ ] Security logging is enabled
- [ ] Error messages don't leak sensitive information
- [ ] File uploads (if any) are validated and sanitized
- [ ] Database queries use parameterized statements
- [ ] API keys are stored securely (not in code)

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [MDN: Subresource Integrity](https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity)
- [OWASP: Dependency Security](https://owasp.org/www-community/vulnerabilities/Using_Components_with_Known_Vulnerabilities)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)

