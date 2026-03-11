using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace API.Migrations
{
    /// <inheritdoc />
    public partial class InitialCreate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "CameraPlates",
                columns: table => new
                {
                    CameraIP = table.Column<string>(type: "nvarchar(450)", nullable: false),
                    PlateNumber = table.Column<string>(type: "nvarchar(max)", nullable: true),
                    X1 = table.Column<int>(type: "int", nullable: false),
                    Y1 = table.Column<int>(type: "int", nullable: false),
                    X2 = table.Column<int>(type: "int", nullable: false),
                    Y2 = table.Column<int>(type: "int", nullable: false),
                    LastUpdate = table.Column<DateTime>(type: "datetime2", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_CameraPlates", x => x.CameraIP);
                });

            migrationBuilder.CreateTable(
                name: "Department",
                columns: table => new
                {
                    DepartmentId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    Name = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK__Departme__B2079BED22FBEE13", x => x.DepartmentId);
                });

            migrationBuilder.CreateTable(
                name: "Exception_Reason",
                columns: table => new
                {
                    ReasonId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    ReasonCode = table.Column<string>(type: "varchar(50)", unicode: false, maxLength: 50, nullable: false),
                    Description = table.Column<string>(type: "nvarchar(200)", maxLength: 200, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK__Exceptio__A4F8C0E71D19C4D0", x => x.ReasonId);
                });

            migrationBuilder.CreateTable(
                name: "Gate",
                columns: table => new
                {
                    GateId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    GateName = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: false),
                    Location = table.Column<string>(type: "nvarchar(200)", maxLength: 200, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK__Gate__9582C65020BEEB76", x => x.GateId);
                });

            migrationBuilder.CreateTable(
                name: "GuestProfile",
                columns: table => new
                {
                    GuestId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    FullName = table.Column<string>(type: "nvarchar(150)", maxLength: 150, nullable: false),
                    Phone = table.Column<string>(type: "nvarchar(20)", maxLength: 20, nullable: true),
                    DefaultLicensePlate = table.Column<string>(type: "nvarchar(20)", maxLength: 20, nullable: true),
                    FaceImageURL = table.Column<string>(type: "nvarchar(300)", maxLength: 300, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK__GuestPro__0C423C12B547B8BB", x => x.GuestId);
                });

            migrationBuilder.CreateTable(
                name: "Position",
                columns: table => new
                {
                    PositionId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    Name = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK__Position__60BB9A79F338CF82", x => x.PositionId);
                });

            migrationBuilder.CreateTable(
                name: "VehicleType",
                columns: table => new
                {
                    VehicleTypeId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    TypeName = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK__VehicleT__9F449643A4120859", x => x.VehicleTypeId);
                });

            migrationBuilder.CreateTable(
                name: "Camera",
                columns: table => new
                {
                    CameraId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    CameraName = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: false),
                    GateId = table.Column<int>(type: "int", nullable: true),
                    CameraType = table.Column<string>(type: "varchar(50)", unicode: false, maxLength: 50, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK__Camera__F971E0C89B981B26", x => x.CameraId);
                    table.ForeignKey(
                        name: "FK_Camera_Gate",
                        column: x => x.GateId,
                        principalTable: "Gate",
                        principalColumn: "GateId");
                });

            migrationBuilder.CreateTable(
                name: "Employee",
                columns: table => new
                {
                    EmployeeId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    DepartmentId = table.Column<int>(type: "int", nullable: true),
                    PositionId = table.Column<int>(type: "int", nullable: true),
                    FullName = table.Column<string>(type: "nvarchar(150)", maxLength: 150, nullable: false),
                    Phone = table.Column<string>(type: "nvarchar(20)", maxLength: 20, nullable: true),
                    Email = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: true),
                    FaceImageURL = table.Column<string>(type: "nvarchar(300)", maxLength: 300, nullable: true),
                    Status = table.Column<bool>(type: "bit", nullable: true, defaultValue: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK__Employee__7AD04F1101CCCAF2", x => x.EmployeeId);
                    table.ForeignKey(
                        name: "FK_Employee_Department",
                        column: x => x.DepartmentId,
                        principalTable: "Department",
                        principalColumn: "DepartmentId");
                    table.ForeignKey(
                        name: "FK_Employee_Position",
                        column: x => x.PositionId,
                        principalTable: "Position",
                        principalColumn: "PositionId");
                });

            migrationBuilder.CreateTable(
                name: "AppUsers",
                columns: table => new
                {
                    UserId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    Username = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: false),
                    PasswordHash = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: false),
                    FullName = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: true),
                    Role = table.Column<string>(type: "nvarchar(20)", maxLength: 20, nullable: false, defaultValue: "Staff"),
                    IsActive = table.Column<bool>(type: "bit", nullable: false, defaultValue: true),
                    CreatedAt = table.Column<DateTime>(type: "datetime2", nullable: false, defaultValueSql: "(getutcdate())"),
                    EmployeeId = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_AppUsers", x => x.UserId);
                    table.ForeignKey(
                        name: "FK_AppUser_Employee",
                        column: x => x.EmployeeId,
                        principalTable: "Employee",
                        principalColumn: "EmployeeId",
                        onDelete: ReferentialAction.SetNull);
                });

            migrationBuilder.CreateTable(
                name: "Pre_Registration",
                columns: table => new
                {
                    RegistrationId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    GuestId = table.Column<int>(type: "int", nullable: true),
                    HostEmployeeId = table.Column<int>(type: "int", nullable: true),
                    ExpectedLicensePlate = table.Column<string>(type: "nvarchar(20)", maxLength: 20, nullable: true),
                    ExpectedTimeIn = table.Column<DateTime>(type: "datetime", nullable: false),
                    ExpectedTimeOut = table.Column<DateTime>(type: "datetime", nullable: false),
                    Status = table.Column<string>(type: "varchar(50)", unicode: false, maxLength: 50, nullable: true, defaultValue: "PENDING"),
                    NumberOfVisitors = table.Column<int>(type: "int", nullable: false, defaultValue: 1),
                    CreatedAt = table.Column<DateTime>(type: "datetime", nullable: false, defaultValueSql: "(getdate())")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK__Pre_Regi__6EF58810D0B7AD86", x => x.RegistrationId);
                    table.ForeignKey(
                        name: "FK_PreReg_Employee",
                        column: x => x.HostEmployeeId,
                        principalTable: "Employee",
                        principalColumn: "EmployeeId");
                    table.ForeignKey(
                        name: "FK_PreReg_Guest",
                        column: x => x.GuestId,
                        principalTable: "GuestProfile",
                        principalColumn: "GuestId");
                });

            migrationBuilder.CreateTable(
                name: "Registration_Links",
                columns: table => new
                {
                    LinkId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    Token = table.Column<string>(type: "varchar(32)", unicode: false, maxLength: 32, nullable: false),
                    HostEmployeeId = table.Column<int>(type: "int", nullable: false),
                    ExpiredAt = table.Column<DateTime>(type: "datetime", nullable: false),
                    IsUsed = table.Column<bool>(type: "bit", nullable: false, defaultValue: false),
                    CreatedAt = table.Column<DateTime>(type: "datetime", nullable: false, defaultValueSql: "(getdate())")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Registration_Links", x => x.LinkId);
                    table.ForeignKey(
                        name: "FK_RegistrationLink_Employee",
                        column: x => x.HostEmployeeId,
                        principalTable: "Employee",
                        principalColumn: "EmployeeId",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Vehicle",
                columns: table => new
                {
                    VehicleId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    LicensePlate = table.Column<string>(type: "nvarchar(20)", maxLength: 20, nullable: false),
                    VehicleTypeId = table.Column<int>(type: "int", nullable: true),
                    EmployeeId = table.Column<int>(type: "int", nullable: true),
                    Description = table.Column<string>(type: "nvarchar(200)", maxLength: 200, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK__Vehicle__476B54920FBE48B7", x => x.VehicleId);
                    table.ForeignKey(
                        name: "FK_Vehicle_Employee",
                        column: x => x.EmployeeId,
                        principalTable: "Employee",
                        principalColumn: "EmployeeId");
                    table.ForeignKey(
                        name: "FK_Vehicle_Type",
                        column: x => x.VehicleTypeId,
                        principalTable: "VehicleType",
                        principalColumn: "VehicleTypeId");
                });

            migrationBuilder.CreateTable(
                name: "Access_Log",
                columns: table => new
                {
                    LogId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    Timestamp = table.Column<DateTime>(type: "datetime", nullable: true, defaultValueSql: "(getdate())"),
                    Direction = table.Column<string>(type: "varchar(10)", unicode: false, maxLength: 10, nullable: false),
                    GateId = table.Column<int>(type: "int", nullable: true),
                    CameraId = table.Column<int>(type: "int", nullable: true),
                    CapturedLicensePlate = table.Column<string>(type: "nvarchar(20)", maxLength: 20, nullable: true),
                    CapturedFaceImageURL = table.Column<string>(type: "nvarchar(300)", maxLength: 300, nullable: true),
                    EmployeeId = table.Column<int>(type: "int", nullable: true),
                    RegistrationId = table.Column<int>(type: "int", nullable: true),
                    ResultStatus = table.Column<string>(type: "varchar(20)", unicode: false, maxLength: 20, nullable: false),
                    IsBypass = table.Column<bool>(type: "bit", nullable: true, defaultValue: false),
                    ExceptionReasonId = table.Column<int>(type: "int", nullable: true),
                    Note = table.Column<string>(type: "nvarchar(500)", maxLength: 500, nullable: true),
                    EntryLogId = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK__Access_L__5E548648F597543A", x => x.LogId);
                    table.ForeignKey(
                        name: "FK_AccessLog_Camera",
                        column: x => x.CameraId,
                        principalTable: "Camera",
                        principalColumn: "CameraId");
                    table.ForeignKey(
                        name: "FK_AccessLog_Employee",
                        column: x => x.EmployeeId,
                        principalTable: "Employee",
                        principalColumn: "EmployeeId");
                    table.ForeignKey(
                        name: "FK_AccessLog_EntryLog",
                        column: x => x.EntryLogId,
                        principalTable: "Access_Log",
                        principalColumn: "LogId");
                    table.ForeignKey(
                        name: "FK_AccessLog_ExceptionReason",
                        column: x => x.ExceptionReasonId,
                        principalTable: "Exception_Reason",
                        principalColumn: "ReasonId");
                    table.ForeignKey(
                        name: "FK_AccessLog_Gate",
                        column: x => x.GateId,
                        principalTable: "Gate",
                        principalColumn: "GateId");
                    table.ForeignKey(
                        name: "FK_AccessLog_PreRegistration",
                        column: x => x.RegistrationId,
                        principalTable: "Pre_Registration",
                        principalColumn: "RegistrationId");
                });

            migrationBuilder.CreateTable(
                name: "Visitor_Details",
                columns: table => new
                {
                    VisitorDetailId = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    RegistrationId = table.Column<int>(type: "int", nullable: false),
                    FullName = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: false),
                    IdCardNumber = table.Column<string>(type: "nvarchar(20)", maxLength: 20, nullable: true),
                    ExpectedFaceImage = table.Column<string>(type: "nvarchar(max)", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Visitor_Details", x => x.VisitorDetailId);
                    table.ForeignKey(
                        name: "FK_VisitorDetail_PreRegistration",
                        column: x => x.RegistrationId,
                        principalTable: "Pre_Registration",
                        principalColumn: "RegistrationId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.InsertData(
                table: "AppUsers",
                columns: new[] { "UserId", "CreatedAt", "EmployeeId", "FullName", "IsActive", "PasswordHash", "Role", "Username" },
                values: new object[] { 1, new DateTime(2024, 1, 1, 0, 0, 0, 0, DateTimeKind.Utc), null, "Quản trị viên", true, "$2a$11$PrhXqO.4Z0Cj8lccCWYCq.4QcZfTJnxeUc.TfOwRcOBV7tQfW3p4S", "Admin", "admin" });

            migrationBuilder.CreateIndex(
                name: "IX_Access_Log_CameraId",
                table: "Access_Log",
                column: "CameraId");

            migrationBuilder.CreateIndex(
                name: "IX_Access_Log_EmployeeId",
                table: "Access_Log",
                column: "EmployeeId");

            migrationBuilder.CreateIndex(
                name: "IX_Access_Log_EntryLogId",
                table: "Access_Log",
                column: "EntryLogId");

            migrationBuilder.CreateIndex(
                name: "IX_Access_Log_ExceptionReasonId",
                table: "Access_Log",
                column: "ExceptionReasonId");

            migrationBuilder.CreateIndex(
                name: "IX_Access_Log_GateId",
                table: "Access_Log",
                column: "GateId");

            migrationBuilder.CreateIndex(
                name: "IX_Access_Log_RegistrationId",
                table: "Access_Log",
                column: "RegistrationId");

            migrationBuilder.CreateIndex(
                name: "IX_AppUsers_EmployeeId",
                table: "AppUsers",
                column: "EmployeeId",
                unique: true,
                filter: "[EmployeeId] IS NOT NULL");

            migrationBuilder.CreateIndex(
                name: "IX_AppUsers_Username",
                table: "AppUsers",
                column: "Username",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Camera_GateId",
                table: "Camera",
                column: "GateId");

            migrationBuilder.CreateIndex(
                name: "IX_Employee_DepartmentId",
                table: "Employee",
                column: "DepartmentId");

            migrationBuilder.CreateIndex(
                name: "IX_Employee_PositionId",
                table: "Employee",
                column: "PositionId");

            migrationBuilder.CreateIndex(
                name: "UQ__Exceptio__A6278DA348D14177",
                table: "Exception_Reason",
                column: "ReasonCode",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Pre_Registration_GuestId",
                table: "Pre_Registration",
                column: "GuestId");

            migrationBuilder.CreateIndex(
                name: "IX_Pre_Registration_HostEmployeeId",
                table: "Pre_Registration",
                column: "HostEmployeeId");

            migrationBuilder.CreateIndex(
                name: "IX_Registration_Links_HostEmployeeId",
                table: "Registration_Links",
                column: "HostEmployeeId");

            migrationBuilder.CreateIndex(
                name: "IX_Registration_Links_Token",
                table: "Registration_Links",
                column: "Token",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Vehicle_EmployeeId",
                table: "Vehicle",
                column: "EmployeeId");

            migrationBuilder.CreateIndex(
                name: "IX_Vehicle_VehicleTypeId",
                table: "Vehicle",
                column: "VehicleTypeId");

            migrationBuilder.CreateIndex(
                name: "UQ__Vehicle__026BC15CB8D416A0",
                table: "Vehicle",
                column: "LicensePlate",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Visitor_Details_RegistrationId",
                table: "Visitor_Details",
                column: "RegistrationId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Access_Log");

            migrationBuilder.DropTable(
                name: "AppUsers");

            migrationBuilder.DropTable(
                name: "CameraPlates");

            migrationBuilder.DropTable(
                name: "Registration_Links");

            migrationBuilder.DropTable(
                name: "Vehicle");

            migrationBuilder.DropTable(
                name: "Visitor_Details");

            migrationBuilder.DropTable(
                name: "Camera");

            migrationBuilder.DropTable(
                name: "Exception_Reason");

            migrationBuilder.DropTable(
                name: "VehicleType");

            migrationBuilder.DropTable(
                name: "Pre_Registration");

            migrationBuilder.DropTable(
                name: "Gate");

            migrationBuilder.DropTable(
                name: "Employee");

            migrationBuilder.DropTable(
                name: "GuestProfile");

            migrationBuilder.DropTable(
                name: "Department");

            migrationBuilder.DropTable(
                name: "Position");
        }
    }
}
