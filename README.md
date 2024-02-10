This repo contains all the extra material regarding submission 


The folder window_heuristic_source_code contains the code implementing the window size heuristic in both techniques SAT and MILP. To test some examples for the window heuristic you should first start a container in the following way

  `cd window_heuristic_source_code && make rundocker`

After you can run examples of milp models using window heuristic with the following command.

  `sage submission_scripts/example_milp_window_heuristic.py`

In the file chacha_boomerang_checker.py you can find the script used to check the practical boomerang distinguishers for ChaCha mentioned in the paper in Table 1. To run it use the following command

  `python3 submission_scripts/chacha_boomerang_checker.py`

The trails related to speck are in the folder `speck_results`

