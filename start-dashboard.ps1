param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8790,
    [switch]$NoReload,
    [switch]$Reload
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectRoot "backend"
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

function Initialize-JobSupport {
    if (-not $IsWindows) {
        return
    }
    if ("DashboardJobSupport" -as [type]) {
        return
    }

    Add-Type -TypeDefinition @"
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

public static class DashboardJobSupport
{
    private const int JobObjectExtendedLimitInformation = 9;
    private const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000;

    [StructLayout(LayoutKind.Sequential)]
    private struct JOBOBJECT_BASIC_LIMIT_INFORMATION
    {
        public long PerProcessUserTimeLimit;
        public long PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass;
        public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct IO_COUNTERS
    {
        public ulong ReadOperationCount;
        public ulong WriteOperationCount;
        public ulong OtherOperationCount;
        public ulong ReadTransferCount;
        public ulong WriteTransferCount;
        public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION
    {
        public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
        public IO_COUNTERS IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr CreateJobObject(IntPtr lpJobAttributes, string lpName);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool SetInformationJobObject(
        IntPtr hJob,
        int jobObjectInfoClass,
        IntPtr lpJobObjectInfo,
        uint cbJobObjectInfoLength);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool AssignProcessToJobObject(IntPtr hJob, IntPtr hProcess);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr hObject);

    public static IntPtr CreateKillOnCloseJob()
    {
        IntPtr job = CreateJobObject(IntPtr.Zero, null);
        if (job == IntPtr.Zero)
        {
            throw new Win32Exception(Marshal.GetLastWin32Error(), "Unable to create a Windows Job Object.");
        }

        var info = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;

        int length = Marshal.SizeOf<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>();
        IntPtr infoPtr = Marshal.AllocHGlobal(length);
        try
        {
            Marshal.StructureToPtr(info, infoPtr, false);
            if (!SetInformationJobObject(job, JobObjectExtendedLimitInformation, infoPtr, (uint)length))
            {
                throw new Win32Exception(Marshal.GetLastWin32Error(), "Unable to configure kill-on-close for the Job Object.");
            }
            return job;
        }
        catch
        {
            CloseHandle(job);
            throw;
        }
        finally
        {
            Marshal.FreeHGlobal(infoPtr);
        }
    }

    public static void AssignProcess(IntPtr job, IntPtr processHandle)
    {
        if (job == IntPtr.Zero)
        {
            throw new ArgumentException("Invalid Job Object handle.", nameof(job));
        }
        if (processHandle == IntPtr.Zero)
        {
            throw new ArgumentException("Invalid process handle.", nameof(processHandle));
        }
        if (!AssignProcessToJobObject(job, processHandle))
        {
            throw new Win32Exception(Marshal.GetLastWin32Error(), "Unable to assign the child process to the Job Object.");
        }
    }

    public static void Close(IntPtr handle)
    {
        if (handle != IntPtr.Zero)
        {
            CloseHandle(handle);
        }
    }
}
"@
}

function Pause-OnError {
    param([string]$Message)

    Write-Host $Message -ForegroundColor Red
    if ($Host.Name -eq "ConsoleHost" -and -not $env:CI) {
        Read-Host "Premi INVIO per chiudere"
    }
    exit 1
}

function Stop-ProcessTree {
    param([System.Diagnostics.Process]$Process)

    if ($null -eq $Process) {
        return
    }

    try {
        if ($Process.HasExited) {
            return
        }
    }
    catch {
        return
    }

    if ($IsWindows) {
        Start-Process -FilePath "taskkill.exe" -ArgumentList @("/PID", $Process.Id, "/T", "/F") -NoNewWindow -Wait | Out-Null
        return
    }

    Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
}

Write-Host "Starting MCP Dashboard on http://$BindHost`:$Port" -ForegroundColor Cyan
Write-Host "Project root: $projectRoot"

$pythonExe = $null
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = (Get-Command python).Source
}
else {
    Pause-OnError "Python non trovato. Installa Python o crea una .venv in $projectRoot"
}

& $pythonExe -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('fastapi') and importlib.util.find_spec('uvicorn') else 1)" | Out-Null
$depsExitCode = $LASTEXITCODE
if ($depsExitCode -ne 0) {
    Pause-OnError "Dipendenze mancanti su $pythonExe. Esegui: pip install -r $backendDir\requirements.txt"
}

$enableReload = $false
if ($Reload) {
    $enableReload = $true
}
elseif ($NoReload) {
    $enableReload = $false
}

$reloadArgs = @()
if ($enableReload) {
    $reloadArgs += "--reload"
}

$dashboardProcess = $null
$jobHandle = [IntPtr]::Zero

try {
    $uvicornArgs = @("-m", "uvicorn", "app.main:app", "--host", $BindHost, "--port", $Port) + $reloadArgs

    if ($IsWindows) {
        Initialize-JobSupport
        $jobHandle = [DashboardJobSupport]::CreateKillOnCloseJob()
    }

    $dashboardProcess = Start-Process -FilePath $pythonExe -ArgumentList $uvicornArgs -WorkingDirectory $backendDir -NoNewWindow -PassThru

    if ($IsWindows -and $jobHandle -ne [IntPtr]::Zero) {
        [DashboardJobSupport]::AssignProcess($jobHandle, $dashboardProcess.Handle)
    }

    $dashboardProcess.WaitForExit()
    if ($dashboardProcess.ExitCode -ne 0) {
        Pause-OnError "Uvicorn terminato con exit code $($dashboardProcess.ExitCode). Controlla dipendenze e configurazione."
    }
}
catch {
    Pause-OnError ("Avvio dashboard fallito: " + $_.Exception.Message)
}
finally {
    Stop-ProcessTree -Process $dashboardProcess
    if ($IsWindows -and $jobHandle -ne [IntPtr]::Zero) {
        [DashboardJobSupport]::Close($jobHandle)
    }
}
