import sys
import argparse
import random as rand

def parse_crp_commandline():
	parser = argparse.ArgumentParser(description='Demonstration of CRP', conflict_handler='resolve')
	parser.add_argument('--customers', help='Number of customers', required=True)
	parser.add_argument('--alpha', help='Value of alpha', required=True)
	args = vars(parser.parse_args())
	return args['customers'], args['alpha']

def chinese_restaurant_process(customers, alpha):
	tables_count = []
	i = 0

	for cur_customer in range(customers):
		length = len(tables_count)
		prob_at_table = [0] * (length + 1)

		for i in range(length):
			prob_at_table[i] = tables_count[i] / (cur_customer + alpha)
		prob_at_table[length] = (alpha * 1.0) / (cur_customer + alpha)

		total_prob = sum(prob_at_table)
		cur_random_prob = rand.random()
		assigned_table = -1
		prob_measure = 0
		while (cur_random_prob > prob_measure) and (assigned_table <= length):
			assigned_table += 1
			prob_measure += (prob_at_table[assigned_table] / total_prob)

		if assigned_table == length:
			tables_count.append(0)
		tables_count[assigned_table] += 1
		cur_customer += 1

		#print "tables_count: ", tables_count
		#print "prob_at_table: ", prob_at_table
		#print "cur_random_prob: ", cur_random_prob
		#print "assigned_table: ", assigned_table
		#print "----------------"

if __name__ == "__main__":
	customers, alpha = parse_crp_commandline()
	chinese_restaurant_process(int(customers), float(alpha))
