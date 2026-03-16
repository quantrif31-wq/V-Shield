/**
 * Vietnamese Name Validator
 * 
 * Validate và chuẩn hóa họ tên tiếng Việt:
 * - Chỉ chứa chữ cái (bao gồm Unicode tiếng Việt) và khoảng trắng
 * - Ít nhất 2 từ (họ + tên), mỗi từ ≥ 2 ký tự
 * - Không chứa số, ký tự đặc biệt
 * - Độ dài: 4–50 ký tự (sau khi trim)
 * 
 * Tương đương Python: re.match(r'^[a-zA-ZÀ-ỹ]{2,}(\s[a-zA-ZÀ-ỹ]{2,})+$', name)
 */

// Regex cho phép chữ cái Latin + toàn bộ dấu tiếng Việt (Unicode block)
// Tương đương Python: [a-zA-ZÀ-ỹĐđ]
const VIETNAMESE_CHAR = /[a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂẾưăạảấầẩẫậắằẳẵặẹẻẽềềểếỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪễệỉịọỏốồổỗộớờởỡợụủứừỬỮỰỲỴÝỶỸửữựỳỵýỷỹ]/

// Regex validate toàn bộ họ tên: ít nhất 2 từ, mỗi từ >= 2 chữ cái tiếng Việt
const FULL_NAME_PATTERN = /^[a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂẾưăạảấầẩẫậắằẳẵặẹẻẽềềểếỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪễệỉịọỏốồổỗộớờởỡợụủứừỬỮỰỲỴÝỶỸửữựỳỵýỷỹ]{2,}(\s[a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂẾưăạảấầẩẫậắằẳẵặẹẻẽềềểếỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪễệỉịọỏốồổỗộớờởỡợụủứừỬỮỰỲỴÝỶỸửữựỳỵýỷỹ]{2,})+$/

// Regex kiểm tra ký tự không hợp lệ (số, ký tự đặc biệt)
const INVALID_CHARS = /[^a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂẾưăạảấầẩẫậắằẳẵặẹẻẽềềểếỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪễệỉịọỏốồổỗộớờởỡợụủứừỬỮỰỲỴÝỶỸửữựỳỵýỷỹ\s]/

/**
 * Chuẩn hóa họ tên tiếng Việt:
 * - Trim khoảng trắng đầu/cuối
 * - Gộp khoảng trắng liên tiếp
 * - Viết hoa chữ đầu mỗi từ
 * 
 * @param {string} name - Họ tên thô
 * @returns {string} Họ tên đã chuẩn hóa
 */
export function normalizeVietnameseName(name) {
    if (!name || typeof name !== 'string') return ''
    return name
        .trim()
        .replace(/\s+/g, ' ')  // Gộp khoảng trắng thừa
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ')
}

/**
 * Validate họ tên tiếng Việt.
 * 
 * @param {string} name - Họ tên cần validate
 * @returns {{ isValid: boolean, error: string, normalizedName: string }}
 *   - isValid: họ tên có hợp lệ không
 *   - error: thông báo lỗi (rỗng nếu hợp lệ)
 *   - normalizedName: họ tên đã chuẩn hóa
 */
export function validateVietnameseName(name) {
    const result = { isValid: false, error: '', normalizedName: '' }

    if (!name || typeof name !== 'string' || !name.trim()) {
        result.error = 'Vui lòng nhập họ và tên'
        return result
    }

    const normalized = normalizeVietnameseName(name)
    result.normalizedName = normalized

    // Kiểm tra độ dài
    if (normalized.length < 4) {
        result.error = 'Họ tên quá ngắn (tối thiểu 4 ký tự)'
        return result
    }
    if (normalized.length > 50) {
        result.error = 'Họ tên quá dài (tối đa 50 ký tự)'
        return result
    }

    // Kiểm tra ký tự không hợp lệ (số, ký tự đặc biệt)
    if (INVALID_CHARS.test(normalized)) {
        result.error = 'Họ tên không được chứa số hoặc ký tự đặc biệt'
        return result
    }

    // Kiểm tra format: ít nhất 2 từ, mỗi từ >= 2 chữ cái
    if (!FULL_NAME_PATTERN.test(normalized)) {
        const words = normalized.split(' ').filter(w => w.length > 0)
        if (words.length < 2) {
            result.error = 'Vui lòng nhập đầy đủ họ và tên (ít nhất 2 từ)'
            return result
        }
        const shortWord = words.find(w => w.length < 2)
        if (shortWord) {
            result.error = `Mỗi từ trong tên phải có ít nhất 2 ký tự`
            return result
        }
        result.error = 'Họ tên không hợp lệ'
        return result
    }

    result.isValid = true
    return result
}
