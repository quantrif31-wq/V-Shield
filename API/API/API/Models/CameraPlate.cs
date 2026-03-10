using System;
using System.ComponentModel.DataAnnotations;

namespace API.Models
{
    public class CameraPlate
    {
        [Key]
        public string CameraIP { get; set; } = null!;

        public string? PlateNumber { get; set; }

        public int X1 { get; set; }
        public int Y1 { get; set; }
        public int X2 { get; set; }
        public int Y2 { get; set; }

        public DateTime LastUpdate { get; set; }
    }
}