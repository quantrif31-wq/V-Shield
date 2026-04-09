using System;
using System.Collections.Generic;
using API.Models;
using Microsoft.EntityFrameworkCore;

namespace API.Data;

public partial class ApplicationDbContext : DbContext
{
    public ApplicationDbContext()
    {
    }

    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public virtual DbSet<AccessLog> AccessLogs { get; set; }

    public virtual DbSet<Camera> Cameras { get; set; }
    public virtual DbSet<CameraPlate> CameraPlates { get; set; }

    public virtual DbSet<Department> Departments { get; set; }

    public virtual DbSet<Employee> Employees { get; set; }

    public virtual DbSet<ExceptionReason> ExceptionReasons { get; set; }

    public virtual DbSet<Gate> Gates { get; set; }

    public virtual DbSet<GuestProfile> GuestProfiles { get; set; }

    public virtual DbSet<Position> Positions { get; set; }

    public virtual DbSet<PreRegistration> PreRegistrations { get; set; }

    public virtual DbSet<Vehicle> Vehicles { get; set; }

    public virtual DbSet<VehicleType> VehicleTypes { get; set; }

    public virtual DbSet<AppUser> AppUsers { get; set; }
    // Thêm vào ApplicationDbContext.cs
    public virtual DbSet<RegistrationLink> RegistrationLinks { get; set; }
    public virtual DbSet<VisitorDetail> VisitorDetails { get; set; }
    public virtual DbSet<EmployeeFaceVideo> EmployeeFaceVideos { get; set; }
    public virtual DbSet<EmployeeFaceModel> EmployeeFaceModels { get; set; }
    public virtual DbSet<EmployeeDynamicQr> EmployeeDynamicQrs { get; set; }
    public virtual DbSet<DynamicQrScanLog> DynamicQrScanLogs { get; set; }
    public virtual DbSet<PendingGateSync> PendingGateSyncs { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<AccessLog>(entity =>
        {
            entity.HasKey(e => e.LogId).HasName("PK__Access_L__5E548648F597543A");

            entity.Property(e => e.IsBypass).HasDefaultValue(false);
            entity.Property(e => e.Timestamp).HasDefaultValueSql("(getdate())");

            entity.HasOne(d => d.Camera).WithMany(p => p.AccessLogs).HasConstraintName("FK_AccessLog_Camera");

            entity.HasOne(d => d.Employee).WithMany(p => p.AccessLogs).HasConstraintName("FK_AccessLog_Employee");

            entity.HasOne(d => d.EntryLog).WithMany(p => p.InverseEntryLog).HasConstraintName("FK_AccessLog_EntryLog");

            entity.HasOne(d => d.ExceptionReason).WithMany(p => p.AccessLogs).HasConstraintName("FK_AccessLog_ExceptionReason");

            entity.HasOne(d => d.Gate).WithMany(p => p.AccessLogs).HasConstraintName("FK_AccessLog_Gate");

            entity.HasOne(d => d.Registration).WithMany(p => p.AccessLogs).HasConstraintName("FK_AccessLog_PreRegistration");
        });

        modelBuilder.Entity<Camera>(entity =>
        {
            entity.HasKey(e => e.CameraId).HasName("PK__Camera__F971E0C89B981B26");

            entity.HasOne(d => d.Gate).WithMany(p => p.Cameras).HasConstraintName("FK_Camera_Gate");
        });

        modelBuilder.Entity<Department>(entity =>
        {
            entity.HasKey(e => e.DepartmentId).HasName("PK__Departme__B2079BED22FBEE13");
        });

        modelBuilder.Entity<Employee>(entity =>
        {
            entity.HasKey(e => e.EmployeeId).HasName("PK__Employee__7AD04F1101CCCAF2");

            entity.Property(e => e.Status).HasDefaultValue(true);

            entity.HasOne(d => d.Department).WithMany(p => p.Employees).HasConstraintName("FK_Employee_Department");

            entity.HasOne(d => d.Position).WithMany(p => p.Employees).HasConstraintName("FK_Employee_Position");
        });

        modelBuilder.Entity<ExceptionReason>(entity =>
        {
            entity.HasKey(e => e.ReasonId).HasName("PK__Exceptio__A4F8C0E71D19C4D0");
        });

        modelBuilder.Entity<Gate>(entity =>
        {
            entity.HasKey(e => e.GateId).HasName("PK__Gate__9582C65020BEEB76");
        });

        modelBuilder.Entity<GuestProfile>(entity =>
        {
            entity.HasKey(e => e.GuestId).HasName("PK__GuestPro__0C423C12B547B8BB");
        });

        modelBuilder.Entity<Position>(entity =>
        {
            entity.HasKey(e => e.PositionId).HasName("PK__Position__60BB9A79F338CF82");
        });

        modelBuilder.Entity<PreRegistration>(entity =>
        {
            entity.HasKey(e => e.RegistrationId).HasName("PK__Pre_Regi__6EF58810D0B7AD86");

            entity.Property(e => e.Status).HasDefaultValue("PENDING");

            entity.HasOne(d => d.Guest).WithMany(p => p.PreRegistrations).HasConstraintName("FK_PreReg_Guest");

            entity.HasOne(d => d.HostEmployee).WithMany(p => p.PreRegistrations).HasConstraintName("FK_PreReg_Employee");
            entity.HasMany(e => e.VisitorDetails)
          .WithOne(v => v.Registration)
          .HasForeignKey(v => v.RegistrationId)
          .OnDelete(DeleteBehavior.Cascade)
          .HasConstraintName("FK_VisitorDetail_PreRegistration");
            entity.Property(e => e.NumberOfVisitors).HasDefaultValue(1);
            entity.Property(e => e.CreatedAt).HasDefaultValueSql("(getdate())");
        });
        modelBuilder.Entity<RegistrationLink>(entity =>
{
    entity.HasKey(e => e.LinkId);
    entity.HasIndex(e => e.Token).IsUnique();
    entity.Property(e => e.IsUsed).HasDefaultValue(false);
    entity.Property(e => e.CreatedAt).HasDefaultValueSql("(getdate())");

    entity.HasOne(e => e.HostEmployee)
          .WithMany()
          .HasForeignKey(e => e.HostEmployeeId)
          .OnDelete(DeleteBehavior.Restrict)
          .HasConstraintName("FK_RegistrationLink_Employee");
});

        // THÊM: config VisitorDetail
        modelBuilder.Entity<VisitorDetail>(entity =>
        {
            entity.HasKey(e => e.VisitorDetailId);

            entity.HasOne(e => e.Registration)
                  .WithMany(r => r.VisitorDetails)
                  .HasForeignKey(e => e.RegistrationId)
                  .OnDelete(DeleteBehavior.Cascade)
                  .HasConstraintName("FK_VisitorDetail_PreRegistration");
        });

        modelBuilder.Entity<Vehicle>(entity =>
        {
            entity.HasKey(e => e.VehicleId).HasName("PK__Vehicle__476B54920FBE48B7");

            entity.HasOne(d => d.Employee).WithMany(p => p.Vehicles).HasConstraintName("FK_Vehicle_Employee");

            entity.HasOne(d => d.VehicleType).WithMany(p => p.Vehicles).HasConstraintName("FK_Vehicle_Type");
            entity.Property(e => e.ParkingStatus)
          .HasMaxLength(10)
          .HasDefaultValue("OUT");
        });

        modelBuilder.Entity<VehicleType>(entity =>
        {
            entity.HasKey(e => e.VehicleTypeId).HasName("PK__VehicleT__9F449643A4120859");
        });

        modelBuilder.Entity<AppUser>(entity =>
        {
            entity.HasKey(e => e.UserId);
            entity.HasIndex(e => e.Username).IsUnique();
            entity.Property(e => e.Role).HasDefaultValue("Staff");
            entity.Property(e => e.IsActive).HasDefaultValue(true);
            entity.Property(e => e.CreatedAt).HasDefaultValueSql("(getutcdate())");

            // Quan hệ 1-1: một AppUser gắn với tối đa một Employee
            entity.HasOne(u => u.Employee)
                  .WithOne(e => e.AppUser)
                  .HasForeignKey<AppUser>(u => u.EmployeeId)
                  .OnDelete(DeleteBehavior.SetNull)
                  .HasConstraintName("FK_AppUser_Employee");
        });
        modelBuilder.Entity<EmployeeFaceVideo>(entity =>
        {
            entity.HasKey(e => e.Id);

            entity.Property(e => e.FileName)
                  .HasMaxLength(255);

            entity.Property(e => e.FilePath)
                  .HasMaxLength(500);

            entity.Property(e => e.CreatedAt)
                  .HasDefaultValueSql("(getdate())");

            entity.HasOne(e => e.Employee)
                  .WithMany()
                  .HasForeignKey(e => e.EmployeeId)
                  .OnDelete(DeleteBehavior.Cascade)
                  .HasConstraintName("FK_EmployeeFaceVideo_Employee");
        });
        modelBuilder.Entity<EmployeeFaceModel>(entity =>
        {
            entity.HasKey(e => e.Id);

            entity.Property(e => e.ModelFileName)
                  .HasMaxLength(255);

            entity.Property(e => e.ModelPath)
                  .HasMaxLength(500);

            entity.Property(e => e.CreatedAt)
                  .HasDefaultValueSql("(getdate())");

            entity.HasOne(e => e.Employee)
                  .WithMany()
                  .HasForeignKey(e => e.EmployeeId)
                  .OnDelete(DeleteBehavior.Cascade)
                  .HasConstraintName("FK_EmployeeFaceModel_Employee");
        });

        modelBuilder.Entity<Department>(entity =>
        {
            entity.HasKey(e => e.DepartmentId).HasName("PK__Departme__B2079BED22FBEE13");

            entity.HasData(
                new Department { DepartmentId = 1, Name = "Phòng Kỹ thuật" },
                new Department { DepartmentId = 2, Name = "Phòng Nhân sự" },
                new Department { DepartmentId = 3, Name = "Phòng Bảo vệ" }
            );
        });

        modelBuilder.Entity<Position>(entity =>
        {
            entity.HasKey(e => e.PositionId).HasName("PK__Position__60BB9A79F338CF82");

            entity.HasData(
                new Position { PositionId = 1, Name = "Nhân viên" },
                new Position { PositionId = 2, Name = "Trưởng nhóm" },
                new Position { PositionId = 3, Name = "Bảo vệ" }
            );
        });

        modelBuilder.Entity<Employee>(entity =>
        {
            entity.HasKey(e => e.EmployeeId).HasName("PK__Employee__7AD04F1101CCCAF2");

            entity.Property(e => e.Status).HasDefaultValue(true);

            entity.HasOne(d => d.Department)
                  .WithMany(p => p.Employees)
                  .HasConstraintName("FK_Employee_Department");

            entity.HasOne(d => d.Position)
                  .WithMany(p => p.Employees)
                  .HasConstraintName("FK_Employee_Position");

            entity.HasData(
                new Employee
                {
                    EmployeeId = 1,
                    DepartmentId = 1,
                    PositionId = 1,
                    FullName = "Phạm Ngọc Hoài Anh",
                    Phone = "0900000001",
                    Email = "a@company.local",
                    FaceImageUrl = "/images/employees/a.jpg",
                    Status = true
                },
                new Employee
                {
                    EmployeeId = 2,
                    DepartmentId = 1,
                    PositionId = 2,
                    FullName = "Phạm Văn Thành",
                    Phone = "0900000002",
                    Email = "b@company.local",
                    FaceImageUrl = "/images/employees/b.jpg",
                    Status = true
                },
                new Employee
                {
                    EmployeeId = 3,
                    DepartmentId = 2,
                    PositionId = 1,
                    FullName = "Hà Mạnh Hùng",
                    Phone = "0900000003",
                    Email = "c@company.local",
                    FaceImageUrl = "/images/employees/c.jpg",
                    Status = true
                },
                new Employee
                {
                    EmployeeId = 4,
                    DepartmentId = 3,
                    PositionId = 3,
                    FullName = "Vũ Tiến Đạt",
                    Phone = "0900000004",
                    Email = "d@company.local",
                    FaceImageUrl = "/images/employees/d.jpg",
                    Status = true
                },
                new Employee
                {
                    EmployeeId = 5,
                    DepartmentId = 3,
                    PositionId = 3,
                    FullName = "Nguyễn Quốc Việt",
                    Phone = "0900000005",
                    Email = "e@company.local",
                    FaceImageUrl = "/images/employees/e.jpg",
                    Status = true
                }
            );
        });
        modelBuilder.Entity<EmployeeDynamicQr>(entity =>
        {
            entity.HasKey(e => e.Id);

            entity.HasIndex(e => e.EmployeeId).IsUnique();

            entity.Property(e => e.SecretKey)
                  .HasMaxLength(200)
                  .IsRequired();

            entity.Property(e => e.TimeStepSeconds)
                  .HasDefaultValue(30);

            entity.Property(e => e.Digits)
                  .HasDefaultValue(6);

            entity.Property(e => e.IsActive)
                  .HasDefaultValue(true);

            entity.Property(e => e.CreatedAt)
                  .HasDefaultValueSql("(getutcdate())");

            entity.HasOne(e => e.Employee)
                  .WithMany()
                  .HasForeignKey(e => e.EmployeeId)
                  .OnDelete(DeleteBehavior.Cascade)
                  .HasConstraintName("FK_EmployeeDynamicQr_Employee");
        });

        modelBuilder.Entity<DynamicQrScanLog>(entity =>
        {
            entity.HasKey(e => e.Id);

            entity.Property(e => e.QrPayload)
                  .HasMaxLength(500)
                  .IsRequired();

            entity.Property(e => e.Message)
                  .HasMaxLength(500);

            entity.Property(e => e.ScannerDevice)
                  .HasMaxLength(200);

            entity.Property(e => e.ScannedAt)
                  .HasDefaultValueSql("(getutcdate())");
        });
        modelBuilder.Entity<PendingGateSync>(entity =>
        {
            entity.HasKey(e => e.PendingGateSyncId);

            entity.Property(e => e.LicensePlate)
                  .HasMaxLength(20)
                  .IsRequired();

            entity.Property(e => e.Description)
                  .HasMaxLength(500);

            entity.Property(e => e.Status)
                  .HasMaxLength(20)
                  .HasDefaultValue("PENDING");

            entity.Property(e => e.CreatedAt)
                  .HasDefaultValueSql("(getutcdate())");

            entity.Property(e => e.SyncDueAt)
                  .HasDefaultValueSql("(getutcdate())");

            entity.Property(e => e.LastError)
                  .HasMaxLength(500);

            entity.Property(e => e.RemoteMessage)
                  .HasMaxLength(500);

            entity.Property(e => e.RetryCount)
                  .HasDefaultValue(0);
        });
        OnModelCreatingPartial(modelBuilder);
    }

    partial void OnModelCreatingPartial(ModelBuilder modelBuilder);
}
