import sys
import math
import argparse
import subprocess
import numpy as np

'''
Function to print the value of the attributes passed through the command line.
@param1: Expert labels file
@param2: Output file
@param3: Value of alpha_prime
@param4: Value of beta
@return: None
'''
def print_init_values(expertfile, outputfile, alpha_prime, beta):
	print "expertlabelfile: ", expertfile
	print "outputfile: ", outputfile
	print "alphaprime: ", alpha_prime
	print "beta: ", beta

'''
Function to parse command line arguments passed to the script.
@params: None
@return: A dictionary with keys as command line options and values
		 as their corresponding values passed in command value.
'''
def parse_wcrp_commandline():
	parser = argparse.ArgumentParser(description='Demonstration of WCRP', conflict_handler='resolve')
	parser.add_argument('--expertlabelfile', help='Path to expert labels file', required=True)
	parser.add_argument('--outputfile', help='Output assignment file name', required=True)
	parser.add_argument('--alphaprime', help='Value of alpha prime', required=False)
	parser.add_argument('--beta', help='Value of beta, default value 0.5', required=False)
	args = vars(parser.parse_args())
	return args

'''
Function to set default values for command line arguments, in case
any of the optional arguments are missing.
@param1: A dictionary with keys as command line options and values
		 as their corresponding values passed in command value.
@return: Final values of the command line options.
'''
def set_parameter_values(args):
	expertfile = args['expertlabelfile']
	outputfile = args['outputfile']

	if args['beta'] != None:
		beta = args['beta']
	else:
		beta = 0.5

	if args['alphaprime'] != None:
		alpha_prime = args['alphaprime']
	else:
		alpha_prime = np.random.gamma(1, 100)
	return expertfile, outputfile, alpha_prime, beta

'''
Function to execute any bash command in python.
@param1: Bash command to be executed.
@return: Output of the bash command.
'''
def execute_bash_command(bash_cmd):
	output = subprocess.check_output(['bash','-c', bash_cmd])
	return output

'''
Function to load the expert provided labels into a list.
@param1: List into which the file content is loaded.
		 expert_labels[exercise_id] = skill_id
@param2: File name/path to the expert label dataset file.
@return: None
'''
def load_expert_labels(expert_labels, expert_labels_filename):
	fobj = open(expert_labels_filename, "r")
	index = 0
	for line in fobj:
		expert_labels[index] = int(line)
		index += 1

'''
Function to compute logarithm of a value to base e(=2.718)
@param1: Value to be computed log of.
@return: Log of value to the base e
'''
def logbase_e(value):
	if value != 0:
		return math.log(value)
	else:
		return 0.0

'''
Function to group the exercises obtained from expert labels
file into their respective skills.
@param1: List of skill id values for each exercise as given
		 by the expert.
@param2: Number of exercises as given by expert
@param3: Number of skills as given by expert
@return: 2D numpy array with index as skill id and value as an
		 array of exercises that belong to the skill.
'''
def partition_exercises(expert_labels, num_exercises, num_skills):
	expert_exercise_to_skill_mapping = []
	for i in range(num_skills+1):
		expert_exercise_to_skill_mapping.append([])

	for cur_exercise in range(num_exercises):
		expert_exercise_to_skill_mapping[expert_labels[cur_exercise]+1].append(cur_exercise)
	return np.array(expert_exercise_to_skill_mapping)


'''
Function to calculate the probability of placing the current
exercise under a new skill. Implementation as defined in the
paper.
'''
def log_prob_of_new_table(nskills, log_alpha_prime, log_gamma):
	log_nskills = logbase_e(nskills)
	return (-1.0 * log_nskills) + log_alpha_prime + log_gamma

'''
Function to calculate the value of K for the given customer
affiliation and the set of affiliations present at the table.
Implementation as defined in the paper.
'''
def calculate_kvalue(expert_labels, expert_mapping, num_exercises, wcrp_mapping, nskills, table_id, cur_exercise, customer_affiliation, num_expert_skills, beta):
	gamma = 1 - beta
	num_seated_at_table = len(wcrp_mapping[table_id])
	counts = [0] * (num_expert_skills + 1)

	for i in range(num_seated_at_table):
		counts[expert_labels[i]] += 1
	max_expert_label_count = max(counts)

	if counts[customer_affiliation] == 0:
		k_nr = math.pow(gamma, max_expert_label_count)
	else:
		k_nr = math.pow(gamma, max_expert_label_count - counts[customer_affiliation])

	k_dr = 0.0
	for i in range(1, num_expert_skills + 1):
		k_dr += math.pow(gamma, counts[expert_labels[i]])

	k = (k_nr / k_dr)
	return k

'''
Function to calculate the probability of placing the current
exercise under an already discovered skill. Implementation as
defined in the paper.
'''
def log_prob_of_occupied_table(expert_labels, expert_mapping, num_exercises, wcrp_mapping, table_id, nskills, cur_exercise, num_expert_skills, beta):
	log_nskills = logbase_e(num_expert_skills)
	gamma = 1 - beta
	log_num_customers_at_curtable = logbase_e(len(wcrp_mapping[table_id]))
	customer_affiliation = expert_labels[cur_exercise]

	k = calculate_kvalue(expert_labels, expert_mapping, num_exercises, wcrp_mapping, nskills, table_id, cur_exercise, customer_affiliation, num_expert_skills, beta)
	temp1 = logbase_e(k + (1.0 - k) * gamma)
	temp2 = (1.0 / num_expert_skills) + ((1.0 - (1.0 / num_expert_skills)) * gamma)
	return log_num_customers_at_curtable - log_nskills + temp1 - logbase_e(temp2)

'''
Function to perform the Weighted CRP operation.
@param1: List of skill id values for each exercise as given
		 by the expert.
@param2: 2D numpy array with index as skill id and value as an
		 array of exercises that belong to the skill.
@param3: Number of skills as given by expert.
@param4: Number of exercises as given by expert.
@param5: Value of alpha prime.
@param6: Value of beta.
@return: List of mapping of exercises to skills.
'''
def perform_wcrp(expert_labels, expert_mapping, num_skills, num_exercises, alpha_prime, beta):
	log_alpha_prime = logbase_e(alpha_prime)
	log_gamma = logbase_e(1 - beta)
	wcrp_mapping = []
	num_discovered_skills = 0

	wcrp_mapping.append([])
	for cur_exercise in range(num_exercises):
		occupied_tables_probs = [0] * (num_discovered_skills + 1)
		index = 1
		max_occupied_table_prob = 0.0
		occupied_table_id = 0
		for cur_occupied_table in range(1, num_discovered_skills):
			occupied_tables_probs[index] = math.pow(math.e, log_prob_of_occupied_table(expert_labels, expert_mapping, num_exercises, wcrp_mapping, cur_occupied_table, num_discovered_skills, cur_exercise, num_skills, beta))
			index += 1
		if num_discovered_skills != 0:
			occupied_table_id, max_occupied_table_prob = max(enumerate(occupied_tables_probs),key=lambda x: x[1])

		new_table_prob = math.pow(math.e, log_prob_of_new_table(num_skills, log_alpha_prime, log_gamma))
		if max_occupied_table_prob >= new_table_prob:
			wcrp_mapping[occupied_table_id].append(cur_exercise)
		else:
			wcrp_mapping.append([])
			num_discovered_skills += 1
			wcrp_mapping[num_discovered_skills].append(cur_exercise)

	return wcrp_mapping

'''
Main function to carry out the required sequence of calls.
'''
if __name__ == '__main__':
	args = parse_wcrp_commandline()
	[expertfile, outputfile, alpha_prime, beta] = set_parameter_values(args)
	#print_init_values(expertfile, outputfile, alpha_prime, beta)

	num_exercises = int(execute_bash_command("wc -l " + expertfile + " | cut -d ' ' -f 1"))
	expert_labels = np.zeros(num_exercises, dtype = int)
	load_expert_labels(expert_labels, expertfile)
	num_skills = max(expert_labels) + 1
	#print "Number of skills = ", num_skills
	#print "Number of exercises = ", num_exercises

	expert_mapping = partition_exercises(expert_labels, num_exercises, num_skills)
	#print "expert_mapping: ", expert_mapping

	wcrp_mapping = perform_wcrp(expert_labels, expert_mapping, num_skills, num_exercises, float(alpha_prime), float(beta))
	execute_bash_command("echo " + str(wcrp_mapping[1:]) + " &> " + outputfile)
	#print "wcrp_mapping: ", wcrp_mapping
