const NON_ALPHANUMERIC = /[^A-Z0-9]/g

function normalizeRawPlate(rawPlate) {
    return String(rawPlate || "")
        .toUpperCase()
        .trim()
        .replace(NON_ALPHANUMERIC, "")
}

function formatNumberBlock(numberPart) {
    return numberPart.length === 5
        ? `${numberPart.slice(0, 3)}.${numberPart.slice(3)}`
        : numberPart
}

function analyzePlate(rawPlate) {
    const rawInput = String(rawPlate || "").toUpperCase().trim()
    const compact = normalizeRawPlate(rawPlate)

    const result = {
        rawInput,
        compact,
        cleanedPlate: rawInput,
        isValid: false,
        type: "Unknown"
    }

    if (!compact || compact.length < 7 || compact.length > 9 || !/^\d{2}/.test(compact)) {
        return result
    }

    const province = compact.slice(0, 2)
    const remainder = compact.slice(2)

    const motorcycleMatch = remainder.match(/^([A-Z]\d)(\d{5})$/)
    if (motorcycleMatch) {
        result.cleanedPlate = `${province}${motorcycleMatch[1]}-${formatNumberBlock(motorcycleMatch[2])}`
        result.isValid = true
        result.type = "Motorcycle"
        return result
    }

    const carMatch = remainder.match(/^([A-Z]{1,2})(\d{4,5})$/)
    if (carMatch) {
        result.cleanedPlate = `${province}${carMatch[1]}-${formatNumberBlock(carMatch[2])}`
        result.isValid = true
        result.type = "Car"
        return result
    }

    return result
}

export function optimizeAndValidatePlate(rawPlate) {
    return analyzePlate(rawPlate)
}

export function normalizeLicensePlateLookup(rawPlate) {
    return normalizeRawPlate(rawPlate)
}

export function formatLicensePlateDisplay(rawPlate) {
    const result = analyzePlate(rawPlate)
    return result.isValid ? result.cleanedPlate : String(rawPlate || "").toUpperCase().trim()
}

export function validatePlateFormat(plate) {
    const result = analyzePlate(plate)
    return { isValid: result.isValid, type: result.type }
}

export function getVehicleTypeLabel(type) {
    const map = { Car: "Ô tô", Motorcycle: "Xe máy", Unknown: "Không xác định" }
    return map[type] || "Không xác định"
}
