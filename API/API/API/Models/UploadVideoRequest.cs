using Microsoft.AspNetCore.Http;

namespace API.Models
{
    public class UploadVideoRequest
    {
        public IFormFile File { get; set; }

        public int? EmployeeId { get; set; }
    }
}