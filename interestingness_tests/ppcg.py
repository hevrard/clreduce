#!/usr/bin/env python3

from enum import Enum
from interestingness_tests import base
from interestingness_tests import ppcg_opencl
import os
import sys
import subprocess
import itertools

class PPCGInterestingnessTest(ppcg_opencl.OpenCLInterestingnessTest):
    class OptimisationLevel(Enum):
        unoptimised = "unoptimised"
        optimised = "optimised"
        either = "either"
        all = "all"

    @staticmethod
    def __get_optimisation_level(level_str):
        if level_str is None:
            return PPCGInterestingnessTest.OptimisationLevel.either

        if level_str == "optimised":
            return PPCGInterestingnessTest.OptimisationLevel.optimised
        elif level_str == "unoptimised":
            return PPCGInterestingnessTest.OptimisationLevel.unoptimised
        elif level_str == "either":
            return PPCGInterestingnessTest.OptimisationLevel.either
        elif level_str == "all":
            return PPCGInterestingnessTest.OptimisationLevel.all
        else:
            print("Invalid optimisation level!")
            sys.exit(1)

    @classmethod
    def get_test_options(cls, env):
        options = super().get_test_options(env)

        options["use_oracle"] = env.get("CREDUCE_TEST_USE_ORACLE")
        options["optimisation_level"] = env.get("CREDUCE_TEST_OPTIMISATION_LEVEL")
        options["check_static"] = env.get("CREDUCE_TEST_STATIC")

        return options

    def __init__(self, test_cases, options):
        super().__init__(test_cases, options)

        if "use_oracle" in self.options and self.options["use_oracle"] is not None:
            self.use_oracle = bool(int(self.options["use_oracle"]))
        else:
            self.use_oracle = True

        if "optimisation_level" in self.options:
            self.optimisation_level = self.__get_optimisation_level(self.options["optimisation_level"])
        else:
            self.optimisation_level = self.OptimisationLevel.either

        if "check_static" in self.options:
            self.check_static = bool(int(self.options["check_static"]))
        else:
            self.check_static = True

    def check(self):

        # print("Hugues: start check")

        if self.check_static:
            if not self.is_statically_valid(self.test_case, self.timeout):
                raise base.InvalidTestCaseError("static")

        # print("Hugues: start get_oracle_result")

        # Always use OCLGring as oracle
        oracle = self.get_oracle_result(self.test_case, self.timeout)

        # print("Hugues: oracle is done, and it is :")
        # print(oracle)

        if oracle is None:
            raise base.InvalidTestCaseError("oracle")

        # print("Hugues: start run ppcg host")

        proc = self._run_ppcg_host(self.test_case, self.platform, self.device, self.timeout)

        if proc is None or proc.returncode != 0:
            raise base.InvalidTestCaseError("ppcg_host")

        # if proc.stdout != oracle.stdout:
        #     print("HUGUES: different stdout")

        # # As oclgrind may emit some warning in stderr, remove all lines before "==BEGIN DUMP_ARRAYS=="
        # err_content = oracle.stderr.split("\n")
        # oracle_processed = ""
        # keepline = False
        # for l in err_content:
        #     if "==BEGIN DUMP_ARRAYS==" in l:
        #         keepline = True
        #     if keepline:
        #         oracle_processed += l + "\n"

        # Compare using numdiff
        with open("oracle.stderr", 'w') as f:
            oracle_processed = "\n".join(list(itertools.dropwhile(lambda s : s != "==BEGIN DUMP_ARRAYS==", oracle.stderr.split("\n"))))
            f.write(oracle_processed)
            #f.write(oracle.stderr)

        with open("proc.stderr", 'w') as f:
            proc_processed = "\n".join(list(itertools.dropwhile(lambda s : s != "==BEGIN DUMP_ARRAYS==", proc.stderr.split("\n"))))
            f.write(proc_processed)

        numdiff = os.getenv("NUMDIFF", "numdiff")

        cmd = [
            numdiff,
            "--absolute-tolerance=1e-2",
            "oracle.stderr",
            "proc.stderr"
        ]

        try:
            numdiff_ret = subprocess.run(cmd, universal_newlines=True, timeout=self.timeout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.TimeoutExpired:
            raise base.TestTimeoutError("numdiff")
        # FIXME!!
        except subprocess.SubprocessError:
            print("FIXME: subprocess error with numdiff")
            return False

        #-----
        #huglog = "HUG ##################################################\n"
        #if proc.stdout != oracle.stdout:
        #    huglog += "HUG: interesting: proc.stdout != oracle.stdout\n"
        #    huglog += "HUG: proc.stdout:\n"
        #    huglog += proc.stdout
        #    huglog += "HUG: oracle.stdout:\n"
        #    huglog += oracle.stdout
        #elif numdiff_ret.returncode != 0:
        #    huglog += "HUG: interesting: numdiff_ret.returncode != 0\n"
        #    huglog += "HUG: first lines of oracle.stderr:\n"
        #    with open("oracle.stderr", "r") as f:
        #        content = f.readlines()
        #        for i in range(min(8, len(content))):
        #            huglog += content[i]
        #    huglog += "HUG: first lines of proc.stderr:\n"
        #    with open("proc.stderr", "r") as f:
        #        content = f.readlines()
        #        for i in range(min(8, len(content))):
        #            huglog += content[i]
        #else:
        #    huglog += "HUG: not interesting\n"
        #with open('/data/hevrard/debug_pocl/hugues_reduce/ongoing.log', 'a') as f:
        #    f.write(huglog)
        #-----

        # Compare proc and oracle output
        return (proc.stdout != oracle.stdout) or (numdiff_ret.returncode != 0)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_case = sys.argv[1]
    else:
        test_case = os.environ.get("CREDUCE_TEST_CASE")

    if (test_case is None or
        not os.path.isfile(test_case) or
        not os.access(test_case, os.F_OK)):
        print("Specified test case does not exist!")
        sys.exit(1)

    options = PPCGInterestingnessTest.get_test_options(os.environ)

    test = PPCGInterestingnessTest([test_case], options)
    test.run()
