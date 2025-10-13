import numpy as np

def is_same_variable(value, variable):
    if value == variable:
        return True
    else:
        splitted_value = value.split(':')
        if len(splitted_value) == 3:
            if splitted_value[1] == variable:
                return True
    return False

class Interactions():

    def __init__(self, interactions_first, interactions_second, complete_marginal=True):
        self.interactions = zip(interactions_first, interactions_second)
    
    def transform(self, X, column_labels):
        for first_variable, second_variable in self.interactions:
            first_variable_indices = [i for i, value in enumerate(column_labels) if is_same_variable(value, first_variable)]
            second_variable_indices = [i for i, value in enumerate(column_labels) if is_same_variable(value, second_variable)]
            for fi in first_variable_indices:
                first_split_label = column_labels[fi].split(':')
                if len(first_split_label) == 3:
                    first_column_label_suffix = '::' + str(first_split_label[2])
                else:
                    first_column_label_suffix = ''
                for si in second_variable_indices:
                    second_split_label = column_labels[si].split(':')
                    if len(second_split_label) == 3:
                        second_column_label_suffix = '::' + str(second_split_label[2])
                    else:
                        second_column_label_suffix = ''
                    column_labels.append("interaction:" + first_variable + first_column_label_suffix + ":" + second_variable + second_column_label_suffix)
                    #print(X[:, fi])
                    #print(X[:, si])
                    #print(X[:, fi] * X[:, si])
                    new_column = np.reshape(X[:, fi] * X[:, si], (-1, 1))
                    #print(new_column)
                    X = np.append(X, new_column, axis=1)
        return X