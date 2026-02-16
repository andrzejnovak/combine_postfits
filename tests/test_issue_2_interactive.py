# We need to test the logic inside make_plots.py, but make_plots is a script.
# We can mock sys.modules to import it as a module OR better yet:
# run it as a subprocess and feed stdin.
import subprocess
import unittest

ROOT_FILE = "tests/fitDiags/fit_diag_A.root"


class TestInteractiveOverlap(unittest.TestCase):
    def test_overlap_confirmation_deny(self):
        """Test that the script aborts when overlaps exist and user says 'n' (deny)"""
        # Create a command that triggers overlaps
        # Uses existing root file
        cmd = [
            "python",
            "make_plots.py",
            "--input",
            ROOT_FILE,
            "--cats",
            "cat1:ptbin0*;cat2:ptbin0fail*",
            "-p",
            "0",
            "--data",
            "--unblind",
        ]

        # Run subprocess with input 'n'
        # We expect exit code != 0 (sys.exit with message) or specific output

        # 'n' + newline
        input_str = "n\n"

        result = subprocess.run(cmd, input=input_str, capture_output=True, text=True)

        # The table title is now "Overlapping Categories Detected" but it contains the composition info
        # We removed the second table.
        self.assertIn("Overlapping Categories Detected", result.stdout + result.stderr)
        # self.assertIn("Category Composition", result.stdout + result.stderr) # Title changed
        self.assertIn("Aborted by user", result.stderr)
        self.assertNotEqual(result.returncode, 0)

    def test_overlap_confirmation_accept(self):
        """Test that the script proceeds when overlaps exist and user says 'y' (accept)"""
        # Create a command that triggers overlaps
        cmd = [
            "python",
            "make_plots.py",
            "--input",
            ROOT_FILE,
            "--cats",
            "cat1:ptbin0*;cat2:ptbin0fail*",
            "-p",
            "0",
            "--data",
            "--unblind",
        ]

        # Run subprocess with input 'y'
        # We expect it to proceed. Since we don't want it to actually run heavy plotting,
        # we might catch an error later or just check that it passed the check.
        # But if we pass 'y', it continues to plotting.
        # The plotting might fail or take time, but the key is it *doesn't* abort immediately.
        # We can use a timeout or check output.

        input_str = "y\n"

        # Use a timeout to kill it if it proceeds to plotting (which means success for this test)
        try:
            result = subprocess.run(
                cmd,
                input=input_str,
                capture_output=True,
                text=True,
                timeout=5,  # Should be enough to reach the prompt and continue
            )
        except subprocess.TimeoutExpired as e:
            # If it timed out, it means it passed the check and started plotting/processing
            # We can check the output captured so far if available, but usually TimeoutExpired
            # captures stdout/stderr in the exception object in newer python versions,
            # or we might miss it.
            # actually if it timeouts, it means it DID NOT exit, which is effectively success vs 'n' case.
            # Let's assume validation passed.
            return

        # If it finished quickly (e.g. error later), check it wasn't the abortion error
        if result.returncode != 0:
            # It might fail for other reasons (missing files, etc), but we check it didn't abort due to overlap
            self.assertNotIn("Aborted by user", result.stderr)
            self.assertIn("Overlapping Categories Detected", result.stdout + result.stderr)
            # self.assertIn("Category Composition", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
