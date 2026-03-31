namespace API.DTOs
{
    public class SetCamRequest
    {
        public string? CameraName { get; set; }
        public int? GateId { get; set; }
        public string? CameraType { get; set; }
        public string? StreamUrl { get; set; }
    }
}
