using System.Text.RegularExpressions;

namespace API.Helpers;

public enum LicensePlateVehicleKind
{
    Unknown,
    Car,
    Motorcycle
}

public sealed class LicensePlateInfo
{
    public string RawInput { get; init; } = string.Empty;
    public string LookupKey { get; init; } = string.Empty;
    public string DisplayPlate { get; init; } = string.Empty;
    public bool IsValid { get; init; }
    public LicensePlateVehicleKind VehicleKind { get; init; } = LicensePlateVehicleKind.Unknown;
}

public static class LicensePlateHelper
{
    private static readonly Regex NonAlphaNumericRegex = new("[^A-Z0-9]", RegexOptions.Compiled);

    public static LicensePlateInfo Analyze(string? plate)
    {
        var rawInput = string.IsNullOrWhiteSpace(plate)
            ? string.Empty
            : plate.Trim().ToUpperInvariant();

        if (string.IsNullOrEmpty(rawInput))
        {
            return new LicensePlateInfo();
        }

        var compact = NormalizeLookupKey(rawInput);
        if (string.IsNullOrEmpty(compact))
        {
            return new LicensePlateInfo
            {
                RawInput = rawInput
            };
        }

        if (TryParse(compact, out var province, out var series, out var number, out var vehicleKind))
        {
            return new LicensePlateInfo
            {
                RawInput = rawInput,
                LookupKey = $"{province}{series}{number}",
                DisplayPlate = $"{province}{series}-{FormatNumber(number)}",
                IsValid = true,
                VehicleKind = vehicleKind
            };
        }

        return new LicensePlateInfo
        {
            RawInput = rawInput,
            LookupKey = compact,
            DisplayPlate = rawInput
        };
    }

    public static string NormalizeLookupKey(string? plate)
    {
        if (string.IsNullOrWhiteSpace(plate))
        {
            return string.Empty;
        }

        return NonAlphaNumericRegex.Replace(plate.Trim().ToUpperInvariant(), string.Empty);
    }

    public static string GetFallbackVehicleTypeName(string? plate) =>
        Analyze(plate).VehicleKind switch
        {
            LicensePlateVehicleKind.Car => "Ô tô",
            LicensePlateVehicleKind.Motorcycle => "Xe máy",
            _ => string.Empty
        };

    private static bool TryParse(
        string compact,
        out string province,
        out string series,
        out string number,
        out LicensePlateVehicleKind vehicleKind)
    {
        province = string.Empty;
        series = string.Empty;
        number = string.Empty;
        vehicleKind = LicensePlateVehicleKind.Unknown;

        if (compact.Length < 7 || compact.Length > 9)
        {
            return false;
        }

        if (!compact[..2].All(char.IsDigit))
        {
            return false;
        }

        var remainder = compact[2..];

        if (TryParseMotorcycle(remainder, out series, out number))
        {
            province = compact[..2];
            vehicleKind = LicensePlateVehicleKind.Motorcycle;
            return true;
        }

        if (TryParseCar(remainder, out series, out number))
        {
            province = compact[..2];
            vehicleKind = LicensePlateVehicleKind.Car;
            return true;
        }

        return false;
    }

    private static bool TryParseMotorcycle(string remainder, out string series, out string number)
    {
        series = string.Empty;
        number = string.Empty;

        if (remainder.Length != 7)
        {
            return false;
        }

        var candidateSeries = remainder[..2];
        var candidateNumber = remainder[2..];

        if (!char.IsLetter(candidateSeries[0]) || !char.IsDigit(candidateSeries[1]))
        {
            return false;
        }

        if (candidateNumber.Length != 5 || !candidateNumber.All(char.IsDigit))
        {
            return false;
        }

        series = candidateSeries;
        number = candidateNumber;
        return true;
    }

    private static bool TryParseCar(string remainder, out string series, out string number)
    {
        series = string.Empty;
        number = string.Empty;

        foreach (var seriesLength in new[] { 2, 1 })
        {
            if (remainder.Length <= seriesLength)
            {
                continue;
            }

            var candidateSeries = remainder[..seriesLength];
            var candidateNumber = remainder[seriesLength..];

            if (candidateNumber.Length is not (4 or 5))
            {
                continue;
            }

            if (!candidateSeries.All(char.IsLetter) || !candidateNumber.All(char.IsDigit))
            {
                continue;
            }

            series = candidateSeries;
            number = candidateNumber;
            return true;
        }

        return false;
    }

    private static string FormatNumber(string number) =>
        number.Length == 5
            ? $"{number[..3]}.{number[3..]}"
            : number;
}
