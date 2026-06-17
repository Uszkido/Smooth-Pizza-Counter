using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

class PizzaClub {
    [STAThread]
    static void Main(string[] args) {
        string exeDir   = AppDomain.CurrentDomain.BaseDirectory;
        string vbsPath  = Path.Combine(exeDir, "START_HIDDEN.vbs");
        string setupBat = Path.Combine(exeDir, "SETUP_VENV.bat");
        string venvPy   = Path.Combine(exeDir, "venv_311", "Scripts", "python.exe");

        // If venv not yet created, offer to run setup
        if (!File.Exists(venvPy)) {
            DialogResult r = MessageBox.Show(
                "PizzaClub venv not found.\n\nRun SETUP_VENV.bat first to install Python packages.\n\nOpen setup now?",
                "PizzaClub - Setup Required",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Warning
            );
            if (r == DialogResult.Yes && File.Exists(setupBat)) {
                ProcessStartInfo psi = new ProcessStartInfo("cmd.exe", "/c \"" + setupBat + "\"");
                psi.UseShellExecute = true;
                Process.Start(psi);
            }
            return;
        }

        // Check START_HIDDEN.vbs exists
        if (!File.Exists(vbsPath)) {
            MessageBox.Show(
                "START_HIDDEN.vbs not found in:\n" + exeDir,
                "PizzaClub - Launch Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            );
            return;
        }

        // Launch silently in background
        ProcessStartInfo launch = new ProcessStartInfo();
        launch.FileName        = "wscript.exe";
        launch.Arguments       = "\"" + vbsPath + "\"";
        launch.UseShellExecute = true;
        launch.WindowStyle     = ProcessWindowStyle.Hidden;
        Process.Start(launch);

        // Brief notification
        MessageBox.Show(
            "PizzaClub AI Server is starting in the background.\n\nDashboard will open in your browser shortly.\n\nURL: http://127.0.0.1:8040",
            "PizzaClub - Starting",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        );
    }
}
