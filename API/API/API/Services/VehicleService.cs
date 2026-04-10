using System.Globalization;
using System.Text;
using API.Data;
using API.DTOs;
using API.Helpers;
using API.Models;
using Microsoft.EntityFrameworkCore;

namespace API.Services;

public interface IVehicleService
{
    Task<IEnumerable<VehicleTypeDto>> GetVehicleTypesAsync();
    Task<IEnumerable<VehicleDto>> GetAllAsync();
    Task<VehicleDto?> GetByIdAsync(int vehicleId);
    Task<IEnumerable<VehicleDto>> GetByEmployeeIdAsync(int employeeId);
    Task<VehicleDto?> GetByLicensePlateAsync(string licensePlate);
    Task<VehicleDto> CreateAsync(CreateVehicleDto dto);
    Task<VehicleDto?> UpdateAsync(int vehicleId, UpdateVehicleDto dto);
    Task<bool> DeleteAsync(int vehicleId);
}

public class VehicleService : IVehicleService
{
    private readonly ApplicationDbContext _context;

    public VehicleService(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<IEnumerable<VehicleTypeDto>> GetVehicleTypesAsync()
    {
        await EnsureDefaultVehicleTypesAsync();

        return await _context.VehicleTypes
            .OrderBy(vt => vt.TypeName)
            .Select(vt => new VehicleTypeDto
            {
                VehicleTypeId = vt.VehicleTypeId,
                TypeName = vt.TypeName
            })
            .ToListAsync();
    }

    public async Task<IEnumerable<VehicleDto>> GetAllAsync()
    {
        var vehicles = await _context.Vehicles
            .Include(v => v.Employee)
            .Include(v => v.VehicleType)
            .ToListAsync();

        return vehicles.Select(MapToDto).ToList();
    }

    public async Task<VehicleDto?> GetByIdAsync(int vehicleId)
    {
        var vehicle = await _context.Vehicles
            .Include(v => v.Employee)
            .Include(v => v.VehicleType)
            .FirstOrDefaultAsync(v => v.VehicleId == vehicleId);

        return vehicle == null ? null : MapToDto(vehicle);
    }

    public async Task<IEnumerable<VehicleDto>> GetByEmployeeIdAsync(int employeeId)
    {
        var vehicles = await _context.Vehicles
            .Include(v => v.Employee)
            .Include(v => v.VehicleType)
            .Where(v => v.EmployeeId == employeeId)
            .ToListAsync();

        return vehicles.Select(MapToDto).ToList();
    }

    public async Task<VehicleDto?> GetByLicensePlateAsync(string licensePlate)
    {
        var lookupKey = LicensePlateHelper.NormalizeLookupKey(licensePlate);
        if (string.IsNullOrWhiteSpace(lookupKey))
        {
            return null;
        }

        var vehicles = await _context.Vehicles
            .Include(v => v.Employee)
            .Include(v => v.VehicleType)
            .Where(v => v.LicensePlate != null)
            .ToListAsync();

        var vehicle = vehicles.FirstOrDefault(v =>
            LicensePlateHelper.NormalizeLookupKey(v.LicensePlate) == lookupKey);

        return vehicle == null ? null : MapToDto(vehicle);
    }

    public async Task<VehicleDto> CreateAsync(CreateVehicleDto dto)
    {
        await EnsureDefaultVehicleTypesAsync();

        var plateInfo = LicensePlateHelper.Analyze(dto.LicensePlate);
        if (!plateInfo.IsValid)
        {
            throw new InvalidOperationException("Biển số không đúng định dạng Việt Nam.");
        }

        var existingVehicles = await _context.Vehicles
            .Where(v => v.LicensePlate != null)
            .ToListAsync();

        var duplicateExists = existingVehicles.Any(v =>
            LicensePlateHelper.NormalizeLookupKey(v.LicensePlate) == plateInfo.LookupKey);
        if (duplicateExists)
        {
            throw new InvalidOperationException($"Biển số '{plateInfo.DisplayPlate}' đã được đăng ký.");
        }

        var employeeExists = await _context.Employees
            .AnyAsync(e => e.EmployeeId == dto.EmployeeId);
        if (!employeeExists)
        {
            throw new KeyNotFoundException($"Không tìm thấy nhân viên với ID = {dto.EmployeeId}.");
        }

        var resolvedVehicleTypeId = dto.VehicleTypeId ?? await ResolveVehicleTypeIdByPlateAsync(plateInfo);
        if (resolvedVehicleTypeId.HasValue)
        {
            var vehicleTypeExists = await _context.VehicleTypes
                .AnyAsync(vt => vt.VehicleTypeId == resolvedVehicleTypeId.Value);
            if (!vehicleTypeExists)
            {
                throw new KeyNotFoundException($"Không tìm thấy loại xe với ID = {resolvedVehicleTypeId}.");
            }
        }

        var vehicle = new Vehicle
        {
            LicensePlate = plateInfo.DisplayPlate,
            VehicleTypeId = resolvedVehicleTypeId,
            EmployeeId = dto.EmployeeId,
            Description = dto.Description
        };

        _context.Vehicles.Add(vehicle);
        await _context.SaveChangesAsync();

        await _context.Entry(vehicle).Reference(v => v.Employee).LoadAsync();
        await _context.Entry(vehicle).Reference(v => v.VehicleType).LoadAsync();

        return MapToDto(vehicle);
    }

    public async Task<VehicleDto?> UpdateAsync(int vehicleId, UpdateVehicleDto dto)
    {
        await EnsureDefaultVehicleTypesAsync();

        var vehicle = await _context.Vehicles
            .Include(v => v.Employee)
            .Include(v => v.VehicleType)
            .FirstOrDefaultAsync(v => v.VehicleId == vehicleId);

        if (vehicle == null)
        {
            return null;
        }

        LicensePlateInfo? updatedPlateInfo = null;
        if (!string.IsNullOrWhiteSpace(dto.LicensePlate))
        {
            updatedPlateInfo = LicensePlateHelper.Analyze(dto.LicensePlate);
            if (!updatedPlateInfo.IsValid)
            {
                throw new InvalidOperationException("Biển số không đúng định dạng Việt Nam.");
            }

            var otherVehicles = await _context.Vehicles
                .Where(v => v.LicensePlate != null && v.VehicleId != vehicleId)
                .ToListAsync();

            var duplicateExists = otherVehicles.Any(v =>
                LicensePlateHelper.NormalizeLookupKey(v.LicensePlate) == updatedPlateInfo.LookupKey);
            if (duplicateExists)
            {
                throw new InvalidOperationException($"Biển số '{updatedPlateInfo.DisplayPlate}' đã được đăng ký cho xe khác.");
            }

            vehicle.LicensePlate = updatedPlateInfo.DisplayPlate;
        }

        if (dto.EmployeeId.HasValue)
        {
            var employeeExists = await _context.Employees
                .AnyAsync(e => e.EmployeeId == dto.EmployeeId.Value);
            if (!employeeExists)
            {
                throw new KeyNotFoundException($"Không tìm thấy nhân viên với ID = {dto.EmployeeId}.");
            }

            vehicle.EmployeeId = dto.EmployeeId;
        }

        if (dto.VehicleTypeId.HasValue)
        {
            var vehicleTypeExists = await _context.VehicleTypes
                .AnyAsync(vt => vt.VehicleTypeId == dto.VehicleTypeId.Value);
            if (!vehicleTypeExists)
            {
                throw new KeyNotFoundException($"Không tìm thấy loại xe với ID = {dto.VehicleTypeId}.");
            }

            vehicle.VehicleTypeId = dto.VehicleTypeId;
        }
        else if (!vehicle.VehicleTypeId.HasValue)
        {
            var plateInfo = updatedPlateInfo ?? LicensePlateHelper.Analyze(vehicle.LicensePlate);
            vehicle.VehicleTypeId = await ResolveVehicleTypeIdByPlateAsync(plateInfo);
        }

        if (dto.Description != null)
        {
            vehicle.Description = dto.Description;
        }

        await _context.SaveChangesAsync();

        await _context.Entry(vehicle).Reference(v => v.Employee).LoadAsync();
        await _context.Entry(vehicle).Reference(v => v.VehicleType).LoadAsync();

        return MapToDto(vehicle);
    }

    public async Task<bool> DeleteAsync(int vehicleId)
    {
        var vehicle = await _context.Vehicles.FindAsync(vehicleId);
        if (vehicle == null)
        {
            return false;
        }

        _context.Vehicles.Remove(vehicle);
        await _context.SaveChangesAsync();
        return true;
    }

    private async Task EnsureDefaultVehicleTypesAsync()
    {
        var defaults = new[] { "Ô tô", "Xe máy", "Xe đạp", "Xe tải" };
        var existingNames = await _context.VehicleTypes
            .Select(vt => vt.TypeName)
            .ToListAsync();

        var missing = defaults
            .Where(name => !existingNames.Any(existing => string.Equals(existing, name, StringComparison.OrdinalIgnoreCase)))
            .Select(name => new VehicleType { TypeName = name })
            .ToList();

        if (!missing.Any())
        {
            return;
        }

        _context.VehicleTypes.AddRange(missing);
        await _context.SaveChangesAsync();
    }

    private async Task<int?> ResolveVehicleTypeIdByPlateAsync(LicensePlateInfo plateInfo)
    {
        if (!plateInfo.IsValid)
        {
            return null;
        }

        var aliases = plateInfo.VehicleKind switch
        {
            LicensePlateVehicleKind.Car => new[] { "o to", "xe hoi", "car" },
            LicensePlateVehicleKind.Motorcycle => new[] { "xe may", "motorcycle", "motorbike", "moto" },
            _ => Array.Empty<string>()
        };

        if (aliases.Length == 0)
        {
            return null;
        }

        var vehicleTypes = await _context.VehicleTypes
            .OrderBy(vt => vt.TypeName)
            .ToListAsync();

        var matchedType = vehicleTypes.FirstOrDefault(item =>
        {
            var normalizedName = NormalizeVehicleTypeName(item.TypeName);
            return aliases.Any(alias => normalizedName.Contains(alias, StringComparison.Ordinal));
        });

        return matchedType?.VehicleTypeId;
    }

    private static string NormalizeVehicleTypeName(string? name)
    {
        var normalized = (name ?? string.Empty).Normalize(NormalizationForm.FormD);
        var builder = new StringBuilder(normalized.Length);

        foreach (var ch in normalized)
        {
            if (CharUnicodeInfo.GetUnicodeCategory(ch) != UnicodeCategory.NonSpacingMark)
            {
                builder.Append(char.ToLowerInvariant(ch));
            }
        }

        return builder
            .ToString()
            .Normalize(NormalizationForm.FormC)
            .Trim();
    }

    private static VehicleDto MapToDto(Vehicle vehicle)
    {
        var plateInfo = LicensePlateHelper.Analyze(vehicle.LicensePlate);
        var displayPlate = plateInfo.IsValid ? plateInfo.DisplayPlate : vehicle.LicensePlate;
        var fallbackVehicleTypeName = string.IsNullOrWhiteSpace(vehicle.VehicleType?.TypeName)
            ? LicensePlateHelper.GetFallbackVehicleTypeName(vehicle.LicensePlate)
            : vehicle.VehicleType!.TypeName;

        return new VehicleDto
        {
            VehicleId = vehicle.VehicleId,
            LicensePlate = displayPlate,
            VehicleTypeId = vehicle.VehicleTypeId,
            VehicleTypeName = string.IsNullOrWhiteSpace(fallbackVehicleTypeName) ? null : fallbackVehicleTypeName,
            EmployeeId = vehicle.EmployeeId,
            EmployeeFullName = vehicle.Employee?.FullName,
            Description = vehicle.Description
        };
    }
}
