/**
 * Vietnamese License Plate Validator & OCR Error Corrector
 * 
 * Hỗ trợ validate và sửa lỗi OCR cho biển số xe Việt Nam dân sự:
 * - Ô tô:  [2 số tỉnh][1-2 chữ] - [4-5 số]     VD: 30A-123.45, 51LD-1234
 * - Xe máy: [2 số tỉnh] - [1 chữ][1 chữ/số] [4-5 số] VD: 29-A1 123.45, 59-AA 1234
 */

// Từ điển sửa lỗi OCR phổ biến
const CHAR_TO_NUM = { 'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'Z': '2', 'S': '5', 'G': '6', 'B': '8' }
const NUM_TO_CHAR = { '0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B' }

/**
 * Validate và sửa lỗi OCR cho biển số xe Việt Nam.
 * 
 * @param {string} rawPlate - Chuỗi biển số thô (có thể chứa lỗi OCR)
 * @returns {{ rawInput: string, cleanedPlate: string, isValid: boolean, type: string }}
 *   - rawInput: chuỗi gốc sau khi uppercase/trim
 *   - cleanedPlate: biển số đã được làm sạch/sửa lỗi
 *   - isValid: biển số có hợp lệ không
 *   - type: 'Car' | 'Motorcycle' | 'Unknown'
 */
export function optimizeAndValidatePlate(rawPlate) {
    if (!rawPlate || typeof rawPlate !== 'string') {
        return { rawInput: '', cleanedPlate: '', isValid: false, type: 'Unknown' }
    }

    // Làm sạch khoảng trắng thừa và chuyển thành chữ hoa
    rawPlate = rawPlate.toUpperCase().trim()

    // Regex lỏng để tách nhóm — chấp nhận cả chữ và số ở mọi vị trí
    const loosePattern = /^([A-Z0-9]{2})[-\s]*([A-Z0-9]{1,2})[-\s]*([A-Z0-9]{4}|[A-Z0-9]{3}\.?[A-Z0-9]{2})$/
    const match = rawPlate.match(loosePattern)

    let cleanedPlate = rawPlate

    if (match) {
        const provincePart = match[1]
        const seriesPart = match[2]
        const numberPart = match[3]

        // Sửa lỗi mã tỉnh (BẮT BUỘC là số)
        const fixedProvince = provincePart
            .split('')
            .map(c => CHAR_TO_NUM[c] || c)
            .join('')

        // Sửa lỗi phần dãy số đuôi (BẮT BUỘC là số, giữ lại dấu chấm nếu có)
        const fixedNumber = numberPart
            .split('')
            .map(c => c === '.' ? '.' : (CHAR_TO_NUM[c] || c))
            .join('')

        // Sửa lỗi phần Seri (Ký tự đầu tiên BẮT BUỘC là chữ)
        let fixedSeries = NUM_TO_CHAR[seriesPart[0]] || seriesPart[0]
        if (seriesPart.length === 2) {
            // Ký tự thứ 2 có thể là chữ (ô tô) hoặc số (xe máy)
            // Giữ nguyên nhận diện gốc OCR
            fixedSeries += seriesPart[1]
        }

        // Ráp lại thành định dạng chuẩn
        cleanedPlate = `${fixedProvince}-${fixedSeries} ${fixedNumber}`
    }

    // Validate bằng regex chuẩn
    // Ô tô: [1-9][0-9]-[A-Z]{1,2}  [4 số hoặc 3.2 số]
    const carPattern = /^[1-9][0-9]-[A-Z]{1,2}\s*(\d{4,5}|\d{3}\.\d{2})$/
    // Xe máy: [1-9][0-9]-[A-Z][A-Z0-9]  [4 số hoặc 3.2 số]
    const motoPattern = /^[1-9][0-9]-[A-Z][A-Z0-9]\s*(\d{4,5}|\d{3}\.\d{2})$/

    const result = {
        rawInput: rawPlate,
        cleanedPlate,
        isValid: false,
        type: 'Unknown'
    }

    if (carPattern.test(cleanedPlate)) {
        result.isValid = true
        result.type = 'Car'
    } else if (motoPattern.test(cleanedPlate)) {
        result.isValid = true
        result.type = 'Motorcycle'
    }

    return result
}

/**
 * Validate nhanh biển số (không sửa lỗi OCR).
 * Dùng khi biển số đã được nhập thủ công hoặc đã qua xử lý.
 * 
 * @param {string} plate - Biển số đã format
 * @returns {{ isValid: boolean, type: string }}
 */
export function validatePlateFormat(plate) {
    if (!plate || typeof plate !== 'string') {
        return { isValid: false, type: 'Unknown' }
    }

    plate = plate.toUpperCase().trim()

    const carPattern = /^[1-9][0-9]-?[A-Z]{1,2}\s*(\d{4,5}|\d{3}\.\d{2})$/
    const motoPattern = /^[1-9][0-9]-?[A-Z][A-Z0-9]\s*(\d{4,5}|\d{3}\.\d{2})$/

    if (carPattern.test(plate)) return { isValid: true, type: 'Car' }
    if (motoPattern.test(plate)) return { isValid: true, type: 'Motorcycle' }

    return { isValid: false, type: 'Unknown' }
}

/**
 * Lấy nhãn tiếng Việt cho loại xe.
 * @param {string} type - 'Car' | 'Motorcycle' | 'Unknown'
 * @returns {string}
 */
export function getVehicleTypeLabel(type) {
    const map = { Car: 'Ô tô', Motorcycle: 'Xe máy', Unknown: 'Không xác định' }
    return map[type] || 'Không xác định'
}
