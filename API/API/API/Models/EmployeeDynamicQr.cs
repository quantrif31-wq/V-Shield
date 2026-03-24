using System;

namespace API.Models
{
    public class EmployeeDynamicQr
    {
        public int Id { get; set; }

        public int EmployeeId { get; set; }

        public string SecretKey { get; set; } = string.Empty;

        public int TimeStepSeconds { get; set; } = 30;

        public int Digits { get; set; } = 6;

        public bool IsActive { get; set; } = true;

        public long? LastUsedCounter { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        public DateTime? UpdatedAt { get; set; }

        // Navigation property
        public virtual Employee? Employee { get; set; }
    }
}