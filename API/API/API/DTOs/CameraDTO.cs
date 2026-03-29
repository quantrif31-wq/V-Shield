namespace API.DTOs
{
    public class CameraDTO
    {
        public int CameraId { get; set; }
        public string CameraName { get; set; }
        public int? GateId { get; set; }
        public string? CameraType { get; set; }
        public string? StreamUrl { get; set; }
        public string? UrlView { get; set; }

        public string? GateName { get; set; }
    }
}