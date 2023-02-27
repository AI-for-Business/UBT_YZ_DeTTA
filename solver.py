import math
import pandas as pd
from graphviz import Source


# Creates the decision tree. The argument root_id_suffix is necessary to distinguish different nodes
# with the same name by adding the root_id_suffix to the name of the node to create a unique id
# for the node.
# Returns a tuple. The first element is the attribute which was used for splitting and the second element
# is the input for the dot file for the subtree with the splitting node as root. The third element is the
# input for the detailed log file.
def decision_tree_calculation_detailed_log(subset: pd.DataFrame, root_id_suffix: str) -> (str, list[str], list[str]):
    log: list[str] = []  # initialization of the log file
    logs: list[str] = []  # all log files generated by recursively calculating subtrees appended one by another

    # initialization of variables
    n: int = len(subset.index)  # amount of entries
    igs = []  # the information gains for all attributes
    cols: list[str] = subset.columns.values.tolist()  # get a list of all attribute names
    m = len(cols)  # amount of columns

    log.append("General information:")
    log.append("\t|S| = " + str(n))
    log.append("\tremaining columns: " + str(cols))
    log.append("Calculate the entropy of the subset:")

    # retrieve the data to count the rows for the entropy
    target_attr_vals = subset.iloc[:, m-1]  # get a list of all values of the target attribute including duplicates
    target_attr_vals_unique = target_attr_vals.unique()  # get a list of all values of the target attribute excluding duplicates

    # count how often every target attribute occurs
    target_attr_vals_counts = target_attr_vals.value_counts()

    log.append("\tCount the occurrence of each target attribute value:")
    for i in range(len(target_attr_vals_counts)):
        log.append("\t\t" + str(target_attr_vals_counts.keys()[i]) + ": " + str(target_attr_vals_counts[i]))
    log.append("\tCalculate the entropy:")
    entropy_calc = ""  # here the calculation steps for the entropy are saved

    # calculate the entropy for all data points
    entropy: float = 0
    for i in range(len(target_attr_vals_unique)):  # For every distinct value of the target attribute ...
        percentage = target_attr_vals_counts[i] / n  # ... calculate the percentage of its occurence compared to all values ...
        log_percentage = math.log2(percentage)  # ... and calculate the log_2 of the percentage ...
        entropy -= percentage * log_percentage  # ... to multiply the percentage with log_2(percentage) and subtract the result from the current entropy.
        entropy_calc += "(" + str(target_attr_vals_counts[i]) + "/" + str(n) + ")" + " * log_2(" + str(target_attr_vals_counts[i]) + "/" + str(n) + ") + "  # extend our current entropy calculation

    log.append("\t\tEntropy(S) = " + entropy_calc[:-3] + " = " + str(round(entropy, 3)))
    log.append("Calculate the information gain of all attributes:")

    # Calculate the information gain of all attributes.
    for i in range(m-1):  # For every attribute ...
        entropies = []  # ... we save the entropies of all values ...
        ns = []  # ... and we save how many rows we have for every value ...
        vals: list[str] = subset.iloc[:, i].unique()  # ... and get all distinct values for the attribute.

        log.append("\t" + str(cols[i]) + ":")
        log.append("\t\tCalculate the entropy of all values of the attribute:")

        # Calculate the entropy of all values of the attribute.
        for val in vals:  # For every value of the attribute ...
            subset_subset = subset[subset[cols[i]] == val]  # ... we retrieve all rows which contain this value ...
            n_subset = len(subset_subset)  # ... and count the amount of rows for the given subset ...
            target_attr_vals_counts_subset = subset_subset.iloc[:, m-1].value_counts()  # ... and count how often every target attribute value occurs ...
            entropy_for_val = 0 # ... and initialize the entropy.

            log.append("\t\t\t" + str(val) + ":")
            log.append("\t\t\t\tCount the occurrence of each target attribute value:")
            for j in range(len(target_attr_vals_counts_subset)):
                log.append("\t\t\t\t\t" + str(target_attr_vals_counts_subset.keys()[j]) + ": " + str(target_attr_vals_counts_subset[j]))
            log.append("\t\t\t\tCalculate the entropy:")
            entropy_calc = ""  # here the calculation steps for the entropy are saved

            # Calculate the entropy for the given value of the attribute.
            for j in range(len(target_attr_vals_counts_subset)):  # For every value of the target attribute ...
                percentage = target_attr_vals_counts_subset[j] / n_subset  # ... we calculate the percentage it makes out of all values. ...
                log_percentage = math.log2(percentage)  # ... and calculate log_2(percentage) ...
                entropy_for_val -= percentage * log_percentage  # ... and subtract percentage * log_percentage from the current entropy.
                entropy_calc += "(" + str(target_attr_vals_counts_subset[j]) + "/" + str(n_subset) + ")" + " * log_2(" + str(target_attr_vals_counts_subset[j]) + "/" + str(n_subset) + ") + "  # extend our current entropy calculation

            # append our calculated values to our lists
            entropies.append(entropy_for_val)
            ns.append(n_subset)

            log.append("\t\t\t\t\tEntropy(S_" + str(val) + ") = " + entropy_calc[:-3] + " = " + str(round(entropy_for_val, 3)))

        # calculate the information gain of this attribute
        entropies_sum = 0  # the right side of the calculation of the information gain
        for j in range(len(vals)):  # For every value of the attribute ...
            entropies_sum += (ns[j] / n) * entropies[j]  # ... add the entropy normalized by n to our sum of entropies.
        ig = entropy - entropies_sum
        igs.append(ig)

        log.append("\t\tCalculate the information gain for the attribute:")
        ig_calc = ""  # the right side of the calculation of the information gain
        for j in range(len(vals)):
            ig_calc += "(" + str(ns[j]) + "/" + str(n) + ") * Entropy(S_" + str(vals[j]) + ") + "
        log.append("\t\t\tGain(S," + str(cols[i]) + ") = " + ig_calc[:-3] + " = " + str(round(igs[i], 3)))

    # get the best split attribute
    best_index = -1  # initialization
    best_ig = -math.inf  # initialization
    for i in range(m-1):
        if igs[i] > best_ig:
            best_index = i
            best_ig = igs[i]
    split_attr_name = cols[best_index]

    log.append("Determine the best attribute for splitting: ")
    igs_comma_separated = ""  # all information gains separated by commas
    for col in cols[:-1]:
        igs_comma_separated += "Gain(S," + str(col) + "), "
    log.append("\tmax{" + igs_comma_separated[:-2] + "} = Gain(S," + str(split_attr_name) + ") --> split at " + str(split_attr_name))
    log.append("Create the subtree:")
    log.append("\tCreate the node " + str(split_attr_name))
    log.append("\tCreate a child node for every value of " + str(split_attr_name) + ":")

    # Create the graph data.
    dot = []  # the content of the dot file
    split_attr_id = split_attr_name + root_id_suffix  # the id of the split node
    vals: list[str] = subset.iloc[:, best_index].unique()  # get all values of the split attribute
    id_suffix = 0  # the suffix which is added to the id of newly created nodes

    for val in vals:  # Iterate over all values of the split attribute.

        log.append("\t\t" + str(val) + ":")

        val_subset = subset[subset[split_attr_name] == val]  # all rows which have val for the split attribute
        amount_of_different_target_attr_vals = len(val_subset.iloc[:, m-1].unique())  # How many different target attribute values do we have?
        if amount_of_different_target_attr_vals == 1:  # stops the recursion when there is only one target attribute value left (i. e. when we have perfect entropy)
            child_node_name = val_subset.iloc[:, m-1].unique()[0]  # The remaining target attribute value.
            child_node_id = child_node_name + root_id_suffix + str(id_suffix)  # the id of the node which represents the target attribute value

            log.append("\t\t\tThere is only target attribute value left (i. e. we have perfect entropy). --> Create " + str(child_node_name) + " as the child node.")

        elif m == 2:  # stops the recursion if there are no other split attributes left and we have no perfect entropy
            child_node_name = val_subset.iloc[:, m-1].value_counts().keys()[0]  # the target attribute value with the most rows
            child_node_id = child_node_name + root_id_suffix + str(id_suffix)  # the id of the node which represents the target attribute value with the most rows

            log.append("\t\t\tThere is more than one target attribute values left but we have no more attributes for further splits.\n"
                       "\t\t\tChoose the target attribute value with the most occurrences as the child node. --> Create " + str(child_node_name) + " as the child node.")

        else:  # keep splitting attributes
            val_subset = val_subset.drop(columns=[split_attr_name])  # remove the split attribute column from the data set
            return_val = decision_tree_calculation_detailed_log(val_subset, root_id_suffix + str(id_suffix))  # recursively calculate the decision tree with the split attribute as root node
            child_node_name = return_val[0]  # the split attribute one level deeper in the tree
            child_node_id = child_node_name + root_id_suffix + str(id_suffix)
            dot += return_val[1]  # the dot file entries in the subtree

            logs.append("\n\nThis is the log for the creation of the subtree with " + str(child_node_name) + " as the root.")  # necessary so that we know where the returning log belongs to
            logs += return_val[2]  # append the log file of the subtree to the log file for all subtrees
            log.append("\t\t\tThere is more than one target attribute value left (i. e. we have no perfect entropy) and we can perform an additional split.\n"
                       "\t\t\tSplit at the attribute which leads to the highest information gain. --> Create " + str(child_node_name) + " as the child node.")
        log.append("\t\t\tCreate an edge from " + str(split_attr_name) + " to " + str(child_node_name) + " with the label " + str(val) + ".")

        dot.append("\"" + child_node_id + "\" [label=\"" + child_node_name + "\"]")  # the dot file entry for the child node
        dot.append("\"" + split_attr_id + "\" -> \"" + child_node_id + "\" [label=\"" + val + "\"]")  # the dot file entry for the edge between the split attribute and child node
        id_suffix += 1

    return split_attr_name, dot, (log + logs)  # The name of the split attribute and all dot file entries are returned.


# Creates the decision tree. The argument root_id_suffix is necessary to distinguish different nodes
# with the same name by adding the root_id_suffix to the name of the node to create a unique id
# for the node.
# Returns a tuple. The first element is the attribute which was used for splitting and the second element
# is the input for the dot file for the subtree with the splitting node as root. The third element is the
# input for the compact log file.
def decision_tree_calculation_compact_log(subset: pd.DataFrame, root_id_suffix: str) -> (str, list[str], list[str]):
    log: list[str] = []  # initialization of the log file
    logs: list[str] = []  # all log files generated by recursively calculating subtrees appended one by another

    # initialization of variables
    n: int = len(subset.index)  # amount of entries
    igs = []  # the information gains for all attributes
    cols: list[str] = subset.columns.values.tolist()  # get a list of all attribute names
    m = len(cols)  # amount of columns

    log.append("General information:")
    log.append("\t|S| = " + str(n))
    log.append("\tremaining columns: " + str(cols))

    # retrieve the data to count the rows for the entropy
    target_attr_vals = subset.iloc[:, m-1]  # get a list of all values of the target attribute including duplicates
    target_attr_vals_unique = target_attr_vals.unique()  # get a list of all values of the target attribute excluding duplicates

    # count how often every target attribute occurs
    target_attr_vals_counts = target_attr_vals.value_counts()

    entropy_calc = ""  # here the calculation steps for the entropy for the log file are saved

    # calculate the entropy for all data points
    entropy: float = 0
    for i in range(len(target_attr_vals_unique)):  # For every distinct value of the target attribute ...
        percentage = target_attr_vals_counts[i] / n  # ... calculate the percentage of its occurence compared to all values ...
        log_percentage = math.log2(percentage)  # ... and calculate the log_2 of the percentage ...
        entropy -= percentage * log_percentage  # ... to multiply the percentage with log_2(percentage) and subtract the result from the current entropy.
        entropy_calc += "(" + str(target_attr_vals_counts[i]) + "/" + str(n) + ")" + " * log_2(" + str(target_attr_vals_counts[i]) + "/" + str(n) + ") + "  # extend our current entropy calculation

    log.append("Entropy(S) = " + entropy_calc[:-3] + " = " + str(round(entropy, 3)))
    log.append("information gain calculation:")

    # Calculate the information gain of all attributes.
    for i in range(m-1):  # For every attribute ...
        entropies = []  # ... we save the entropies of all values ...
        ns = []  # ... and we save how many rows we have for every value ...
        vals: list[str] = subset.iloc[:, i].unique()  # ... and get all distinct values for the attribute.

        log.append("\t" + str(cols[i]) + ":")

        # Calculate the entropy of all values of the attribute.
        for val in vals:  # For every value of the attribute ...
            subset_subset = subset[subset[cols[i]] == val]  # ... we retrieve all rows which contain this value ...
            n_subset = len(subset_subset)  # ... and count the amount of rows for the given subset ...
            target_attr_vals_counts_subset = subset_subset.iloc[:, m-1].value_counts()  # ... and count how often every target attribute value occurs ...
            entropy_for_val = 0 # ... and initialize the entropy.

            entropy_calc = ""  # here the calculation steps for the entropy for the log file are saved

            # Calculate the entropy for the given value of the attribute.
            for j in range(len(target_attr_vals_counts_subset)):  # For every value of the target attribute ...
                percentage = target_attr_vals_counts_subset[j] / n_subset  # ... we calculate the percentage it makes out of all values. ...
                log_percentage = math.log2(percentage)  # ... and calculate log_2(percentage) ...
                entropy_for_val -= percentage * log_percentage  # ... and subtract percentage * log_percentage from the current entropy.
                entropy_calc += "(" + str(target_attr_vals_counts_subset[j]) + "/" + str(n_subset) + ")" + " * log_2(" + str(target_attr_vals_counts_subset[j]) + "/" + str(n_subset) + ") + "  # extend our current entropy calculation

            # append our calculated values to our lists
            entropies.append(entropy_for_val)
            ns.append(n_subset)

            log.append("\t\tEntropy(S_" + str(val) + ") = " + entropy_calc[:-3] + " = " + str(round(entropy_for_val, 3)))

        # calculate the information gain of this attribute
        entropies_sum = 0  # the right side of the calculation of the information gain
        for j in range(len(vals)):  # For every value of the attribute ...
            entropies_sum += (ns[j] / n) * entropies[j]  # ... add the entropy normalized by n to our sum of entropies.
        ig = entropy - entropies_sum
        igs.append(ig)

        ig_calc = ""  # the right side of the calculation of the information gain
        for j in range(len(vals)):
            ig_calc += "(" + str(ns[j]) + "/" + str(n) + ") * Entropy(S_" + str(vals[j]) + ") + "
        log.append("\t\tGain(S," + str(cols[i]) + ") = " + ig_calc[:-3] + " = " + str(round(igs[i], 3)))

    # get the best split attribute
    best_index = -1  # initialization
    best_ig = -math.inf  # initialization
    for i in range(m-1):
        if igs[i] > best_ig:
            best_index = i
            best_ig = igs[i]
    split_attr_name = cols[best_index]

    igs_comma_separated = ""  # all information gains separated by commas
    for col in cols[:-1]:
        igs_comma_separated += "Gain(S," + str(col) + "), "
    log.append("max{" + igs_comma_separated[:-2] + "} = Gain(S," + str(split_attr_name) + ")")

    # Create the graph data.
    dot = []  # the content of the dot file
    split_attr_id = split_attr_name + root_id_suffix  # the id of the split node
    vals: list[str] = subset.iloc[:, best_index].unique()  # get all values of the split attribute
    id_suffix = 0  # the suffix which is added to the id of newly created nodes

    for val in vals:  # Iterate over all values of the split attribute.
        val_subset = subset[subset[split_attr_name] == val]  # all rows which have val for the split attribute
        amount_of_different_target_attr_vals = len(val_subset.iloc[:, m-1].unique())  # How many different target attribute values do we have?
        if amount_of_different_target_attr_vals == 1:  # stops the recursion when there is only one target attribute value left (i. e. when we have perfect entropy)
            child_node_name = val_subset.iloc[:, m-1].unique()[0]  # The remaining target attribute value.
            child_node_id = child_node_name + root_id_suffix + str(id_suffix)  # the id of the node which represents the target attribute value
        elif m == 2:  # stops the recursion if there are no other split attributes left and we have no perfect entropy
            child_node_name = val_subset.iloc[:, m-1].value_counts().keys()[0]  # the target attribute value with the most rows
            child_node_id = child_node_name + root_id_suffix + str(id_suffix)  # the id of the node which represents the target attribute value with the most rows
        else:  # keep splitting attributes
            val_subset = val_subset.drop(columns=[split_attr_name])  # remove the split attribute column from the data set
            return_val = decision_tree_calculation_compact_log(val_subset, root_id_suffix + str(id_suffix))  # recursively calculate the decision tree with the split attribute as root node
            child_node_name = return_val[0]  # the split attribute one level deeper in the tree
            child_node_id = child_node_name + root_id_suffix + str(id_suffix)
            dot += return_val[1]  # the dot file entries in the subtree

            logs.append("\n\nroot = " + str(child_node_name))  # necessary so that we know where the returning log belongs to
            logs += return_val[2]  # append the log file of the subtree to the log file for all subtrees

        dot.append("\"" + child_node_id + "\" [label=\"" + child_node_name + "\"]")  # the dot file entry for the child node
        dot.append("\"" + split_attr_id + "\" -> \"" + child_node_id + "\" [label=\"" + val + "\"]")  # the dot file entry for the edge between the split attribute and child node
        id_suffix += 1

    return split_attr_name, dot, (log + logs)  # The name of the split attribute and all dot file entries are returned.


# Calculates the decision tree returning the dot file and creates depending on the input argument
# either a compact or a detailed log file.
def decision_tree_calculation(df: pd.DataFrame, compact_log: bool):
    # calculation
    if compact_log:
        output = decision_tree_calculation_compact_log(df, "")
    else:
        output = decision_tree_calculation_detailed_log(df, "")

    # create the log file
    log = output[2]
    f = open("log.txt", "w")
    for line in log:
        f.write(line + "\n")
    f.close()

    # create the dot file for the tree
    dot_text = output[1]
    f = open("tree.dot", "w")
    f.write("digraph G {\n")
    for line in dot_text:
        f.write("\t" + line + "\n")
    f.write("}")
    f.close()


# input for tests

# classical play tennis data set
data = {
    "Outlook": ["Sunny", "Sunny", "Overcast", "Rain", "Rain", "Rain", "Overcast",
                "Sunny", "Sunny", "Rain", "Sunny", "Overcast", "Overcast", "Rain"],
    "Temperature": ["Hot", "Hot", "Hot", "Mild", "Cool", "Cool", "Cool",
                    "Mild", "Cool", "Mild", "Mild", "Mild", "Hot", "Mild"],
    "Humidity": ["High", "High", "High", "High", "Normal", "Normal", "Normal",
                 "High", "Normal", "Normal", "Normal", "High", "Normal", "High"],
    "Wind": ["Weak", "Strong", "Weak", "Weak", "Weak", "Strong", "Strong",
             "Weak", "Weak", "Weak", "Strong", "Strong", "Weak", "Strong"],
    "PlayTennis": ["No", "No", "Yes", "Yes", "Yes", "No", "Yes",
                   "No", "Yes", "Yes", "Yes", "Yes", "Yes", "No"]
}

# second data set (notes for Dennis: der gleiche Datensatz, wie aus der 5. KDDM-
# Übung mit einem weiteren Datum am Ende, um den Fall len(cols) == 2 abzudecken
data2 = {
    "Experience": ["1-2", "2-7", ">7", "1-2", ">7", "1-2", "2-7", "2-7", ">7"],
    "Gender": ["m", "m", "f", "f", "m", "m", "f", "m", "f"],
    "Area": ["u", "r", "r", "r", "r", "r", "u", "u", "r"],  # u=urban, r=rural
    "Risk class": ["l", "h", "l", "h", "h", "h", "l", "l", "h"]  # h=high, l=low
}
data_arg: pd.DataFrame = pd.DataFrame(data)  # the dataframe for data
data_arg2: pd.DataFrame = pd.DataFrame(data2)  # the dataframe for data2
root_id_suffix_arg = ""  # second argument of the function


# run the classification algorithm on the data set and get the decision tree and log file
decision_tree_calculation(data_arg, compact_log=True)
# Render the graph from the dot file.
path = 'tree.dot'
Source.from_file(path).view()
