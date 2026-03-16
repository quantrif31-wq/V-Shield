using API.DTOs;
using API.Models;
using API.Data;
using Microsoft.EntityFrameworkCore;

namespace API.Services;

// ==================== INTERFACE ====================
public interface IVehicleService
{
    Task<IEnumerable<VehicleDto>> GetAllAsync();
    Task<VehicleDto?> GetByIdAsync(int vehicleId);
    Task<IEnumerable<VehicleDto>> GetByEmployeeIdAsync(int employeeId);
    Task<VehicleDto?> GetByLicensePlateAsync(string licensePlate);
    Task<VehicleDto> CreateAsync(CreateVehicleDto dto);
    Task<VehicleDto?> UpdateAsync(int vehicleId, UpdateVehicleDto dto);
    Task<bool> DeleteAsync(int vehicleId);
}

// ==================== IMPLEMENTATION ====================
public class VehicleService : IVehicleService
{
    private readonly ApplicationDbContext _context;

    public VehicleService(ApplicationDbContext context)
    {
        _context = context;
    }

    // Lấy tất cả phương tiện
    public async Task<IEnumerable<VehicleDto>> GetAllAsync()
    {
        return await _context.Vehicles
            .Include(v => v.Employee)
            .Include(v => v.VehicleType)
            .Select(v => MapToDto(v))
            .ToListAsync();
    }

    // Lấy phương tiện theo ID
    public async Task<VehicleDto?> GetByIdAsync(int vehicleId)
    {
        var vehicle = await _context.Vehicles
            .Include(v => v.Employee)
            .Include(v => v.VehicleType)
            .FirstOrDefaultAsync(v => v.VehicleId == vehicleId);

        return vehicle == null ? null : MapToDto(vehicle);
    }

    // Lấy phương tiện theo mã nhân viên
    public async Task<IEnumerable<VehicleDto>> GetByEmployeeIdAsync(int employeeId)
    {
        return await _context.Vehicles
            .Include(v => v.Employee)
            .Include(v => v.VehicleType)
            .Where(v => v.EmployeeId == employeeId)
            .Select(v => MapToDto(v))
            .ToListAsync();
    }

    // Lấy phương tiện theo biển số
    public async Task<VehicleDto?> GetByLicensePlateAsync(string licensePlate)
    {
        var vehicle = await _context.Vehicles
            .Include(v => v.Employee)
            .Include(v => v.VehicleType)
            .FirstOrDefaultAsync(v => v.LicensePlate == licensePlate);

        return vehicle == null ? null : MapToDto(vehicle);
    }

    // Tạo mới phương tiện
    public async Task<VehicleDto> CreateAsync(CreateVehicleDto dto)
    {
        // Kiểm tra biển số đã tồn tại chưa
        var existing = await _context.Vehicles
            .AnyAsync(v => v.LicensePlate == dto.LicensePlate);
        if (existing)
            throw new InvalidOperationException($"Biển số '{dto.LicensePlate}' đã được đăng ký.");

        // Kiểm tra nhân viên tồn tại
        var employeeExists = await _context.Employees
            .AnyAsync(e => e.EmployeeId == dto.EmployeeId);
        if (!employeeExists)
            throw new KeyNotFoundException($"Không tìm thấy nhân viên với ID = {dto.EmployeeId}.");

        // Kiểm tra loại xe tồn tại
        if (dto.VehicleTypeId.HasValue)
        {
            var vehicleTypeExists = await _context.VehicleTypes
                .AnyAsync(vt => vt.VehicleTypeId == dto.VehicleTypeId.Value);
            if (!vehicleTypeExists)
                throw new KeyNotFoundException($"Không tìm thấy loại xe với ID = {dto.VehicleTypeId}. Vui lòng kiểm tra bảng VehicleType trong database.");
        }

        var vehicle = new Vehicle
        {
            LicensePlate = dto.LicensePlate.Trim().ToUpper(),
            VehicleTypeId = dto.VehicleTypeId,
            EmployeeId = dto.EmployeeId,
            Description = dto.Description
        };

        _context.Vehicles.Add(vehicle);
        await _context.SaveChangesAsync();

        // Reload với navigation properties
        await _context.Entry(vehicle).Reference(v => v.Employee).LoadAsync();
        await _context.Entry(vehicle).Reference(v => v.VehicleType).LoadAsync();

        return MapToDto(vehicle);
    }

    // Cập nhật phương tiện
    public async Task<VehicleDto?> UpdateAsync(int vehicleId, UpdateVehicleDto dto)
    {
        var vehicle = await _context.Vehicles
            .Include(v => v.Employee)
            .Include(v => v.VehicleType)
            .FirstOrDefaultAsync(v => v.VehicleId == vehicleId);

        if (vehicle == null) return null;

        // Kiểm tra biển số mới không trùng với xe khác
        if (!string.IsNullOrWhiteSpace(dto.LicensePlate))
        {
            var duplicatePlate = await _context.Vehicles
                .AnyAsync(v => v.LicensePlate == dto.LicensePlate && v.VehicleId != vehicleId);
            if (duplicatePlate)
                throw new InvalidOperationException($"Biển số '{dto.LicensePlate}' đã được đăng ký cho xe khác.");

            vehicle.LicensePlate = dto.LicensePlate.Trim().ToUpper();
        }

        // Kiểm tra nhân viên mới tồn tại
        if (dto.EmployeeId.HasValue)
        {
            var employeeExists = await _context.Employees
                .AnyAsync(e => e.EmployeeId == dto.EmployeeId.Value);
            if (!employeeExists)
                throw new KeyNotFoundException($"Không tìm thấy nhân viên với ID = {dto.EmployeeId}.");

            vehicle.EmployeeId = dto.EmployeeId;
        }

        // Kiểm tra loại xe mới tồn tại
        if (dto.VehicleTypeId.HasValue)
        {
            var vehicleTypeExists = await _context.VehicleTypes
                .AnyAsync(vt => vt.VehicleTypeId == dto.VehicleTypeId.Value);
            if (!vehicleTypeExists)
                throw new KeyNotFoundException($"Không tìm thấy loại xe với ID = {dto.VehicleTypeId}. Vui lòng kiểm tra bảng VehicleType trong database.");

            vehicle.VehicleTypeId = dto.VehicleTypeId;
        }

        if (dto.Description != null)
            vehicle.Description = dto.Description;

        await _context.SaveChangesAsync();

        // Reload navigation properties sau khi update
        await _context.Entry(vehicle).Reference(v => v.Employee).LoadAsync();
        await _context.Entry(vehicle).Reference(v => v.VehicleType).LoadAsync();

        return MapToDto(vehicle);
    }

    // Xóa phương tiện
    public async Task<bool> DeleteAsync(int vehicleId)
    {
        var vehicle = await _context.Vehicles.FindAsync(vehicleId);
        if (vehicle == null) return false;

        _context.Vehicles.Remove(vehicle);
        await _context.SaveChangesAsync();
        return true;
    }

    // Helper: Map Entity -> DTO
    private static VehicleDto MapToDto(Vehicle v) => new VehicleDto
    {
        VehicleId = v.VehicleId,
        LicensePlate = v.LicensePlate,
        VehicleTypeId = v.VehicleTypeId,
        VehicleTypeName = v.VehicleType?.TypeName,
        EmployeeId = v.EmployeeId,
        EmployeeFullName = v.Employee?.FullName,
        Description = v.Description
    };
}
