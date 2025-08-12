# This note is to document the modifications made to the original Python script [46]. In this updated version, We've integrated our SAT constraint technique with a window size of 3 for the Speck 48/96 cipher. The number of rounds is set to 8 by default, but this can be adjusted as needed.
import os
import time
import random
from window_size_2_cnf import window_size_2_cnf
from window_size_3_cnf import window_size_3_cnf
from window_size_0_cnf import window_size_0_cnf

FullRound = 24

BlockSize = 128
HalfBlockSize = 64
WeightSize = HalfBlockSize - 1
RotateAlpha = 8 # Right rotate
RotateBeta = 3 # Left rotate

SearchRoundStart = 8
SearchRoundEnd = 9
InitialLowerBound = 30

GroupConstraintChoice = 0

# Parameters for choice 1
GroupNumForChoice1 = 1

DifferentialProbabilityBound = list([])
for i in range(FullRound):
    DifferentialProbabilityBound += [0]

def CountClausesInRoundFunction(Round, Prob, clausenum):
    count = clausenum
    # Nonzero input
    count += 1
    for r in range(Round):
        # Modular constraint (last one bit)
        count += 4
        # Modular constraint (first 15 bits)
        for i in range(HalfBlockSize - 1):
            count += 8
        for i in range(HalfBlockSize - 3):
            count += 256
        # Weight constraint
        for i in range(1, HalfBlockSize):
            count += 5
        # XOR constraint
        for i in range(HalfBlockSize):
            count += 4
    return count

def CountClausesInSequentialEncoding(main_var_num, cardinalitycons, clause_num):
    count = clause_num
    n = main_var_num
    k = cardinalitycons
    if (k > 0):
        count += 1
        for j in range(1, k):
            count += 1
        for i in range(1, n-1):
            count += 3
        for j in range(1, k):
            for i in range(1, n-1):
                count += 2
        count += 1
    if (k == 0):
        for i in range(n):
            count += 1
    return count

def CountClausesForMatsuiStrategy(n, k, left, right, m, clausenum):
    count = clausenum
    if (m > 0):
        if ((left == 0) and (right < n-1)):
            for i in range(1, right + 1):
                count += 1
        if ((left > 0) and (right == n-1)):
            for i in range(0, k-m):
                count += 1
            for i in range(0, k-m+1):
                count += 1
        if ((left > 0) and (right < n-1)):
            for i in range(0, k-m):
                count += 1
    if (m == 0):
        for i in range(left, right + 1):
            count += 1
    return count

def GenSequentialEncoding(x, u, main_var_num, cardinalitycons, fout):
    n = main_var_num
    k = cardinalitycons
    if (k > 0):
        clauseseq = "-" + str(x[0]+1) + " " + str(u[0][0]+1) + " 0" + "\n"
        fout.write(clauseseq)
        for j in range(1, k):
            clauseseq = "-" + str(u[0][j]+1) + " 0" + "\n"
            fout.write(clauseseq)
        for i in range(1, n-1):
            clauseseq = "-" + str(x[i]+1) + " " + str(u[i][0]+1) + " 0" + "\n"
            fout.write(clauseseq)
            clauseseq = "-" + str(u[i-1][0]+1) + " " + str(u[i][0]+1) + " 0" + "\n"
            fout.write(clauseseq)
            clauseseq = "-" + str(x[i]+1) + " " + "-" + str(u[i-1][k-1]+1) + " 0" + "\n"
            fout.write(clauseseq)
        for j in range(1, k):
            for i in range(1, n-1):
                clauseseq = "-" + str(x[i]+1) + " " + "-" + str(u[i-1][j-1]+1) + " " + str(u[i][j]+1) + " 0" + "\n"
                fout.write(clauseseq)
                clauseseq = "-" + str(u[i-1][j]+1) + " " + str(u[i][j]+1) + " 0" + "\n"
                fout.write(clauseseq)
        clauseseq = "-" + str(x[n-1]+1) + " " + "-" + str(u[n-2][k-1]+1) + " 0" + "\n"
        fout.write(clauseseq)
    if (k == 0):
        for i in range(n):
            clauseseq = "-" + str(x[i]+1) + " 0" + "\n"
            fout.write(clauseseq)

def GenMatsuiConstraint(x, u, n, k, left, right, m, fout):
    if (m > 0):
        if ((left == 0) and (right < n-1)):
            for i in range(1, right + 1):
                clauseseq = "-" + str(x[i] + 1) + " " + "-" + str(u[i-1][m-1] + 1) + " 0" + "\n"
                fout.write(clauseseq)
        if ((left > 0) and (right == n-1)):
            for i in range(0, k-m):
                clauseseq = str(u[left-1][i] + 1) + " " + "-" + str(u[right - 1][i+m] + 1) + " 0" + "\n"
                fout.write(clauseseq)
            for i in range(0, k-m+1):
                clauseseq = str(u[left-1][i] + 1) + " " + "-" + str(x[right] + 1) + " " + "-" + str(u[right - 1][i+m-1] + 1) + " 0" + "\n"
                fout.write(clauseseq)
        if ((left > 0) and (right < n-1)):
            for i in range(0, k-m):
                clauseseq = str(u[left-1][i] + 1) + " " + "-" + str(u[right][i+m] + 1) + " 0" + "\n"
                fout.write(clauseseq)
    if (m == 0):
        for i in range(left, right + 1):
            clauseseq = "-" + str(x[i] + 1) + " 0" + "\n"
            fout.write(clauseseq)

def Decision(Round, Probability, MatsuiRoundIndex, MatsuiCount, flag):
    TotalProbability = WeightSize * Round
    count_var_num = 0;
    time_start = time.time()
    # Declare variable
    xin = []
    w = []
    xout = []
    for i in range(Round):
        xin.append([])
        w.append([])
        xout.append([])
        for j in range(BlockSize):
            xin[i].append(0)
        for j in range(WeightSize):
            w[i].append(0)
        for j in range(BlockSize):
            xout[i].append(0)
    # Allocate variables
    for i in range(Round):
        for j in range(BlockSize):
            xin[i][j] = count_var_num
            count_var_num += 1
        for j in range(WeightSize):
            w[i][j] = count_var_num
            count_var_num += 1
    for i in range(Round - 1):
        for j in range(BlockSize):
            xout[i][j] = xin[i + 1][j]
    for i in range(BlockSize):
        xout[Round - 1][i] = count_var_num
        count_var_num += 1
    auxiliary_var_u = []
    for i in range(TotalProbability - 1):
        auxiliary_var_u.append([])
        for j in range(Probability):
            auxiliary_var_u[i].append(count_var_num)
            count_var_num += 1
    # Count the number of clauses in the round function
    count_clause_num = 0
    count_clause_num = CountClausesInRoundFunction(Round, Probability, count_clause_num)
    # Count the number of clauses in the original sequential encoding
    Main_Var_Num = WeightSize * Round
    CardinalityCons = Probability
    count_clause_num = CountClausesInSequentialEncoding(Main_Var_Num, CardinalityCons, count_clause_num)
    # Count the number of clauses for Matsui's strategy
    for matsui_count in range(0, MatsuiCount):
        StartingRound = MatsuiRoundIndex[matsui_count][0]
        EndingRound = MatsuiRoundIndex[matsui_count][1]
        LeftNode = WeightSize * StartingRound
        RightNode = WeightSize * EndingRound - 1
        PartialCardinalityCons = Probability - DifferentialProbabilityBound[StartingRound] - DifferentialProbabilityBound[Round - EndingRound]
        count_clause_num = CountClausesForMatsuiStrategy(Main_Var_Num, CardinalityCons, LeftNode, RightNode, PartialCardinalityCons, count_clause_num)
    # Open file
    file = open("Problem-Round" + str(Round) + "-Probability" + str(Probability) + ".cnf", "w")
    file.write("p cnf " + str(count_var_num) + " " + str(count_clause_num) + "\n")
    # Add constraints to claim nonzero input difference
    clauseseq = ""
    for i in range(BlockSize):
        clauseseq += str(xin[0][i] + 1) + " "
    clauseseq += "0" + "\n"
    file.write(clauseseq)
    # Add constraints for the round function
    for r in range(Round):
        temp = list([])
        for i in range(RotateAlpha):
            temp += [xin[r][i + HalfBlockSize - RotateAlpha]]
        for i in range(RotateAlpha, HalfBlockSize):
            temp += [xin[r][i - RotateAlpha]]
        # Modular constraint (last one bit)
        x1 = temp[HalfBlockSize - 1]
        x2 = xin[r][BlockSize - 1]
        x3 = xout[r][HalfBlockSize - 1]
        # Delete 001
        clauseseq = str(x1 + 1) + " " + str(x2 + 1) + " -" + str(x3 + 1) + " " + "0" + "\n"
        file.write(clauseseq)
        # Delete 010
        clauseseq = str(x1 + 1) + " -" + str(x2 + 1) + " " + str(x3 + 1) + " " + "0" + "\n"
        file.write(clauseseq)
        # Delete 100
        clauseseq = "-" + str(x1 + 1) + " " + str(x2 + 1) + " " + str(x3 + 1) + " " + "0" + "\n"
        file.write(clauseseq)
        # Delete 111
        clauseseq = "-" + str(x1 + 1) + " -" + str(x2 + 1) + " -" + str(x3 + 1) + " " + "0" + "\n"
        file.write(clauseseq)
        # Modular constraint (first 15 bits)
        for i in range(HalfBlockSize - 1):
            a = temp[i + 1]
            b = xin[r][i + 1 + HalfBlockSize]
            c = xout[r][i + 1]
            d = temp[i]
            e = xin[r][i + HalfBlockSize]
            f = xout[r][i]
            # Delete 000 001
            clauseseq = str(a + 1) + " " + str(b + 1) + " " + str(c + 1) + " " + str(d + 1) + " " + str(e + 1) + " -" + str(f + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete 000 010
            clauseseq = str(a + 1) + " " + str(b + 1) + " " + str(c + 1) + " " + str(d + 1) + " -" + str(e + 1) + " " + str(f + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete 000 100
            clauseseq = str(a + 1) + " " + str(b + 1) + " " + str(c + 1) + " -" + str(d + 1) + " " + str(e + 1) + " " + str(f + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete 000 111
            clauseseq = str(a + 1) + " " + str(b + 1) + " " + str(c + 1) + " -" + str(d + 1) + " -" + str(e + 1) + " -" + str(f + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete 111 000
            clauseseq =  "-" + str(a + 1) + " -" + str(b + 1) + " -" + str(c + 1) + " " + str(d + 1) + " " + str(e + 1) + " " + str(f + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete 111 011
            clauseseq =  "-" + str(a + 1) + " -" + str(b + 1) + " -" + str(c + 1) + " " + str(d + 1) + " -" + str(e + 1) + " -" + str(f + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete 111 101
            clauseseq =  "-" + str(a + 1) + " -" + str(b + 1) + " -" + str(c + 1) + " -" + str(d + 1) + " " + str(e + 1) + " -" + str(f + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete 111 110
            clauseseq =  "-" + str(a + 1) + " -" + str(b + 1) + " -" + str(c + 1) + " -" + str(d + 1) + " -" + str(e + 1) + " " + str(f + 1) + " " + "0" + "\n"
            file.write(clauseseq)
        ##Adding Thomas Constraints
        window_size = 3
        #file.write("cThomasss\n")
        for i in range(HalfBlockSize - window_size):
            print("i>>>>>", i)
            x_vars = [0 for _ in range((window_size+1)*3)]
            for j in range(window_size+1):
                print(3*j+0, i+j)
                print(3*j+1, i+j)
                print(3*j+2, i+j)
                x_vars[3*j+0] = temp[i + j] + 1
                x_vars[3*j+1] = xin[r][i + j + HalfBlockSize] + 1
                x_vars[3*j+2] = xout[r][i + j] + 1
            clauseseq = window_size_3_cnf(*x_vars)
            #print(clauseseq)
            file.write(clauseseq)
        #file.write("cendThomas\n")
            #    clauseseq = f'-{a+1} -{b+1} -{c+1} '
            #    clauseseq += f'-{a+1} {b+1} {c+1} '
            #    clauseseq += f'{a+1} -{b+1} {c+1} '
            #    clauseseq += f'{a+1} {b+1} -{c+1} 0'
            #    file.write(clauseseq)
            #    # Delete 000 001
        # Weight constraint
        for i in range(1, HalfBlockSize):
            a = temp[i]
            b = xin[r][i + HalfBlockSize]
            c = xout[r][i]
            d = w[r][i - 1]
            # Delete 1*00
            clauseseq = "-" + str(a + 1) + " " + str(c + 1) + " " + str(d + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete *010
            clauseseq = str(b + 1) + " -" + str(c + 1) + " " + str(d + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete 01*0
            clauseseq = str(a + 1) + " -" + str(b + 1) + " " + str(d + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete 0001
            clauseseq = str(a + 1) + " " + str(b + 1) + " " + str(c + 1) + " -" + str(d + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete 1111
            clauseseq = "-" + str(a + 1) + " -" + str(b + 1) + " -" + str(c + 1) + " -" + str(d + 1) + " " + "0" + "\n"
            file.write(clauseseq)
        # Rotate beta
        temp = list([])
        for i in range(HalfBlockSize - RotateBeta):
            temp += [xin[r][i + HalfBlockSize + RotateBeta]]
        for i in range(HalfBlockSize - RotateBeta, HalfBlockSize):
            temp += [xin[r][i + RotateBeta]]
        # XOR constraint
        for i in range(HalfBlockSize):
            a = temp[i]
            b = xout[r][i]
            c = xout[r][i + HalfBlockSize]
            # Delete 001
            clauseseq = str(a + 1) + " " + str(b + 1) + " -" + str(c + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete 010
            clauseseq = str(a + 1) + " -" + str(b + 1) + " " + str(c + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete 100
            clauseseq = "-" + str(a + 1) + " " + str(b + 1) + " " + str(c + 1) + " " + "0" + "\n"
            file.write(clauseseq)
            # Delete 111
            clauseseq = "-" + str(a + 1) + " -" + str(b + 1) + " -" + str(c + 1) + " " + "0" + "\n"
            file.write(clauseseq)
    # Add constraints for the original sequential encoding
    Main_Vars = list([])
    for r in range(Round):
        for i in range(WeightSize):
            Main_Vars += [w[Round - 1 - r][i]]
    GenSequentialEncoding(Main_Vars, auxiliary_var_u, Main_Var_Num, CardinalityCons, file)
    # Add constraints for Matsui's strategy
    for matsui_count in range(0, MatsuiCount):
        StartingRound = MatsuiRoundIndex[matsui_count][0]
        EndingRound = MatsuiRoundIndex[matsui_count][1]
        LeftNode = WeightSize * StartingRound
        RightNode = WeightSize * EndingRound - 1
        PartialCardinalityCons = Probability - DifferentialProbabilityBound[StartingRound] - DifferentialProbabilityBound[Round - EndingRound]
        GenMatsuiConstraint(Main_Vars, auxiliary_var_u, Main_Var_Num, CardinalityCons, LeftNode, RightNode, PartialCardinalityCons, file)
    file.close()
    # Call solver cryptominisat5
    #order = "cryptominisat5 Problem-Round" + str(Round) + "-Probability" + str(Probability) + ".cnf > Round" + str(Round) + "-Probability" + str(Probability) + "-solution.out"
    # Call solver cadical
    order = "~/Programs/cadical/build/cadical " + "Problem-Round" + str(Round) + "-Probability" + str(Probability) + ".cnf > Round" + str(Round) + "-Probability" + str(Probability) + "-solution.out"
    os.system(order)
    # Extracting results
    order = "sed -n '/s SATISFIABLE/p' Round" + str(Round) + "-Probability" + str(Probability) + "-solution.out > SatSolution.out"
    os.system(order)
    order = "sed -n '/s UNSATISFIABLE/p' Round" + str(Round) + "-Probability" + str(Probability) + "-solution.out > UnsatSolution.out"
    os.system(order)
    satsol = open("SatSolution.out")
    unsatsol = open("UnsatSolution.out")
    satresult = satsol.readlines()
    unsatresult = unsatsol.readlines()
    satsol.close()
    unsatsol.close()
    if ((len(satresult) == 0) and (len(unsatresult) > 0)):
        flag = False
    if ((len(satresult) > 0) and (len(unsatresult) == 0)):
        flag = True
    order = "rm SatSolution.out"
    os.system(order)
    order = "rm UnsatSolution.out"
    os.system(order)
    # Removing cnf file
    #order = "rm Problem-Round" + str(Round) + "-Probability" + str(Probability) + ".cnf"
    os.system(order)
    time_end = time.time()
    # Printing solutions
    if (flag == True):
        print("Round:" + str(Round) + "; Probability: " + str(Probability) + "; Sat; TotalCost: " + str(time_end - time_start))
    else:
        print("Round:" + str(Round) + "; Probability: " + str(Probability) + "; Unsat; TotalCost: " + str(time_end - time_start))
    return flag

# main function
CountProbability = InitialLowerBound
TotalTimeStart = time.time()
for totalround in range(SearchRoundStart, SearchRoundEnd):
    flag = False
    time_start = time.time()
    MatsuiRoundIndex = []
    MatsuiCount = 0
    # Generate Matsui condition under choice 1
    if (GroupConstraintChoice == 1):
        for group in range(0, GroupNumForChoice1):
            for round in range(1, totalround - group + 1):
                MatsuiRoundIndex.append([])
                MatsuiRoundIndex[MatsuiCount].append(group)
                MatsuiRoundIndex[MatsuiCount].append(group + round)
                MatsuiCount += 1
    # Printing Matsui conditions
    file = open("MatsuiCondition.out", "a")
    resultseq = "Round: " + str(totalround) + "; Partial Constraint Num: " + str(MatsuiCount) + "\n"
    file.write(resultseq)
    file.write(str(MatsuiRoundIndex) + "\n")
    file.close()
    while (flag == False):
        flag = Decision(totalround, CountProbability, MatsuiRoundIndex, MatsuiCount, flag)
        CountProbability += 1
        break
    DifferentialProbabilityBound[totalround] = CountProbability - 1
    CountProbability = CountProbability - 1
    time_end = time.time()
    file = open("RunTimeSummarise.out", "a")
    resultseq = "Round: " + str(totalround) + "; Differential Probability: " + str(DifferentialProbabilityBound[totalround]) + "; Runtime: " + str(time_end - time_start) + "\n"
    file.write(resultseq)
    file.close()
print(str(DifferentialProbabilityBound))
TotalTimeEnd = time.time()
print("Total Runtime: " + str(TotalTimeEnd - TotalTimeStart))
file = open("RunTimeSummarise.out", "a")
resultseq = "Total Runtime: " + str(TotalTimeEnd - TotalTimeStart)
file.write(resultseq)




