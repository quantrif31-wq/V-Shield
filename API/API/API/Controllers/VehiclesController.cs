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

    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var vehicles = await _vehicleService.GetAllAsync();
        return Ok(vehicles);
    }

    [HttpGet("{id:int}")]
    public async Task<IActionResult> GetById(int id)
    {
        var vehicle = await _vehicleService.GetByIdAsync(id);
        if (vehicle == null)
        {
            return NotFound(new { message = $"Không tìm thấy phương tiện với ID = {id}." });
        }

        return Ok(vehicle);
    }

    [HttpGet("license-plate/{plate}")]
    public async Task<IActionResult> GetByLicensePlate(string plate)
    {
        var vehicle = await _vehicleService.GetByLicensePlateAsync(plate);
        if (vehicle == null)
        {
            return NotFound(new { message = $"Không tìm thấy phương tiện với biển số '{plate}'." });
        }

        return Ok(vehicle);
    }

    [HttpGet("employee/{employeeId:int}")]
    public async Task<IActionResult> GetByEmployeeId(int employeeId)
    {
        var vehicles = await _vehicleService.GetByEmployeeIdAsync(employeeId);
        return Ok(vehicles);
    }

    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateVehicleDto dto)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

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

    [HttpPut("{id:int}")]
    public async Task<IActionResult> Update(int id, [FromBody] UpdateVehicleDto dto)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        try
        {
            var updated = await _vehicleService.UpdateAsync(id, dto);
            if (updated == null)
            {
                return NotFound(new { message = $"Không tìm thấy phương tiện với ID = {id}." });
            }

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

    [HttpDelete("{id:int}")]
    public async Task<IActionResult> Delete(int id)
    {
        var deleted = await _vehicleService.DeleteAsync(id);
        if (!deleted)
        {
            return NotFound(new { message = $"Không tìm thấy phương tiện với ID = {id}." });
        }

        return NoContent();
    }
}
