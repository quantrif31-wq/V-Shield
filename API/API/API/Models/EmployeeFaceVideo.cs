using System;
using System.ComponentModel.DataAnnotations;

namespace API.Models
{
    public class EmployeeFaceVideo
    {
        [Key]
        public int Id { get; set; }

        public int EmployeeId { get; set; }

        public string FileName { get; set; }

        public string FilePath { get; set; }

        public long FileSize { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.Now;

        public virtual Employee Employee { get; set; }
    }
}
