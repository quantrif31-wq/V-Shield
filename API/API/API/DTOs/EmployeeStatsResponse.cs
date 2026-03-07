namespace API.DTOs;

public class EmployeeSummaryResponse
{
    /// <summary>Tổng số nhân viên trong hệ thống</summary>
    public int TotalEmployees { get; set; }

    /// <summary>Số nhân viên đang hoạt động (Status = true)</summary>
    public int ActiveEmployees { get; set; }

    /// <summary>Số nhân viên ngừng hoạt động (Status = false)</summary>
    public int InactiveEmployees { get; set; }

    /// <summary>Thống kê theo phòng ban</summary>
    public List<DepartmentStatItem> ByDepartment { get; set; } = new();

    /// <summary>Thống kê theo chức vụ</summary>
    public List<PositionStatItem> ByPosition { get; set; } = new();

    /// <summary>Thời điểm tính toán</summary>
    public DateTime CalculatedAt { get; set; }
}

public class DepartmentStatItem
{
    public int? DepartmentId { get; set; }
    public string DepartmentName { get; set; } = "Chưa phân phòng";
    public int TotalCount { get; set; }
    public int ActiveCount { get; set; }
}

public class PositionStatItem
{
    public int? PositionId { get; set; }
    public string PositionName { get; set; } = "Chưa có chức vụ";
    public int TotalCount { get; set; }
    public int ActiveCount { get; set; }
}

/// <summary>Object gửi qua SignalR khi số lượng NV thay đổi</summary>
public class EmployeeCountChangedEvent
{
    public int TotalEmployees { get; set; }
    public int ActiveEmployees { get; set; }
    public string ChangeType { get; set; } = null!; // "created" | "deleted" | "updated"
    public DateTime ChangedAt { get; set; }
}
