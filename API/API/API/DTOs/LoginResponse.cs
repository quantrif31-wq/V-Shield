namespace API.DTOs;

public class LoginResponse
{
    public string Token { get; set; } = null!;
    public string Username { get; set; } = null!;
    public string FullName { get; set; } = null!;
    public string Role { get; set; } = null!;
    public int? EmployeeId { get; set; }
    public DateTime ExpiresAt { get; set; }
}
