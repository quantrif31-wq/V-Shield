using API.DTOs;
using API.Services;
using Microsoft.AspNetCore.Mvc;

namespace API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class VehiclesController : ControllerBase
{
    private readonly IVehicleService _vehicleService;

    public VehiclesController(IVehicleService vehicleService)
    {
        _vehicleService = vehicleService;
    }

    [HttpGet("types")]
    public async Task<IActionResult> GetVehicleTypes()
    {
        var vehicleTypes = await _vehicleService.GetVehicleTypesAsync();
        return Ok(vehicleTypes);
    }

    // GET: api/vehicles
    // Lấy danh sách tất cả phương tiện
    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var vehicles = await _vehicleService.GetAllAsync();
        return Ok(vehicles);
    }

    // GET: api/vehicles/5
    // Lấy phương tiện theo ID
    [HttpGet("{id:int}")]
    public async Task<IActionResult> GetById(int id)
    {
        var vehicle = await _vehicleService.GetByIdAsync(id);
        if (vehicle == null)
            return NotFound(new { message = $"Không tìm thấy phương tiện với ID = {id}." });

        return Ok(vehicle);
    }

    // GET: api/vehicles/license-plate/51A-12345
    // Tra cứu phương tiện theo biển số
    [HttpGet("license-plate/{plate}")]
    public async Task<IActionResult> GetByLicensePlate(string plate)
    {
        var vehicle = await _vehicleService.GetByLicensePlateAsync(plate.ToUpper());
        if (vehicle == null)
            return NotFound(new { message = $"Không tìm thấy phương tiện với biển số '{plate}'." });

        return Ok(vehicle);
    }

    // GET: api/vehicles/employee/10
    // Lấy danh sách phương tiện của một nhân viên
    [HttpGet("employee/{employeeId:int}")]
    public async Task<IActionResult> GetByEmployeeId(int employeeId)
    {
        var vehicles = await _vehicleService.GetByEmployeeIdAsync(employeeId);
        return Ok(vehicles);
    }

    // POST: api/vehicles
    // Đăng ký phương tiện mới
    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateVehicleDto dto)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        try
        {
            var created = await _vehicleService.CreateAsync(dto);
            return CreatedAtAction(nameof(GetById), new { id = created.VehicleId }, created);
        }
        catch (InvalidOperationException ex)
        {
            return Conflict(new { message = ex.Message });
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(new { message = ex.Message });
        }
    }

    // PUT: api/vehicles/5
    // Cập nhật thông tin phương tiện
    [HttpPut("{id:int}")]
    public async Task<IActionResult> Update(int id, [FromBody] UpdateVehicleDto dto)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        try
        {
            var updated = await _vehicleService.UpdateAsync(id, dto);
            if (updated == null)
                return NotFound(new { message = $"Không tìm thấy phương tiện với ID = {id}." });

            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            return Conflict(new { message = ex.Message });
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(new { message = ex.Message });
        }
    }

    // DELETE: api/vehicles/5
    // Xóa đăng ký phương tiện
    [HttpDelete("{id:int}")]
    public async Task<IActionResult> Delete(int id)
    {
        var deleted = await _vehicleService.DeleteAsync(id);
        if (!deleted)
            return NotFound(new { message = $"Không tìm thấy phương tiện với ID = {id}." });

        return NoContent();
    }
}
