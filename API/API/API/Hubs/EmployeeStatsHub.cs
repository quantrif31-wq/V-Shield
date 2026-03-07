using Microsoft.AspNetCore.SignalR;

namespace API.Hubs;

/// <summary>
/// SignalR Hub để push thống kê nhân viên real-time cho client.
/// Client kết nối tới /hubs/employee-stats và lắng nghe sự kiện:
///   - "ReceiveStatsUpdate" : nhận object { currentInsideCount, changedAt }
/// </summary>
public class EmployeeStatsHub : Hub
{
    /// <summary>
    /// Client gọi để tham gia nhóm nhận cập nhật thống kê.
    /// </summary>
    public async Task JoinStatsGroup()
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, "stats");
    }

    /// <summary>
    /// Client gọi để rời nhóm.
    /// </summary>
    public async Task LeaveStatsGroup()
    {
        await Groups.RemoveFromGroupAsync(Context.ConnectionId, "stats");
    }
}
