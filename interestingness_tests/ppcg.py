#!/usr/bin/env python3

from enum import Enum
from interestingness_tests import base
from interestingness_tests import ppcg_opencl
import os
import sys

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

        if self.check_static:
            # No cl_launcher related thing for PPCG
            # if not self.is_valid_cl_launcher_test_case(self.test_case):
            #     raise base.InvalidTestCaseError("cl_launcher")

            if not self.is_statically_valid(self.test_case, self.timeout):
                raise base.InvalidTestCaseError("static")

        # Always use OCLGring as oracle
        oracle = self.get_oracle_result(self.test_case, self.timeout)

        if oracle is None:
            raise base.InvalidTestCaseError("oracle")

        print("HUGUES: done with OCLGRIND, start PPCG")

        proc = self._run_ppcg_host(self.test_case, self.platform, self.device, self.timeout)

        if proc is None or proc.returncode != 0:
            raise base.InvalidTestCaseError("ppcg_host")

        if proc.stdout != oracle.stdout:
            print("HUGUES: different stdout")

        if proc.stderr != oracle.stderr:
            print("HUGUES: different stderr")

        # Compare proc and oracle output
        return (proc.stdout != oracle.stdout) or (proc.stderr != oracle.stderr)

        # print("HUGUES: work in progress")
        # return False

        # if self.use_oracle:
        #     # Implicitly checks if test case is valid in Oclgrind
        #     oracle = self.get_oracle_result(self.test_case, self.timeout)

        #     if self.optimisation_level is self.OptimisationLevel.optimised:
        #         proc_opt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=True)

        #         if proc_opt is None or proc_opt.returncode != 0:
        #             raise base.InvalidTestCaseError("optimised")

        #         return proc_opt.stdout != oracle
        #     elif self.optimisation_level is self.OptimisationLevel.unoptimised:
        #         proc_unopt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=False)

        #         if proc_unopt is None or proc_unopt.returncode != 0:
        #             raise base.InvalidTestCaseError("unoptimised")

        #         return proc_unopt.stdout != oracle
        #     elif self.optimisation_level is self.OptimisationLevel.either:
        #         proc_opt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=True)

        #         if proc_opt is None or proc_opt.returncode != 0:
        #             raise base.InvalidTestCaseError("optimised")

        #         if proc_opt.stdout != oracle:
        #             return True

        #         proc_unopt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=False)

        #         if proc_unopt is None or proc_unopt.returncode != 0:
        #             raise base.InvalidTestCaseError("unoptimised")

        #         if proc_unopt.stdout != oracle:
        #             return True

        #         return False
        #     elif self.optimisation_level is self.OptimisationLevel.all:
        #         proc_opt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=True)

        #         if proc_opt is None or proc_opt.returncode != 0:
        #             raise base.InvalidTestCaseError("optimised")

        #         if proc_opt.stdout == oracle:
        #             return False

        #         proc_unopt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=False)

        #         if proc_unopt is None or proc_unopt.returncode != 0:
        #             raise base.InvalidTestCaseError("unoptimised")

        #         if proc_unopt.stdout == oracle:
        #             return False

        #         return True


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
