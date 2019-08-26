import cv2
import os,glob
import numpy as np 
import pdb
from pylsd.lsd import lsd
from hor_and_ver_merged_lines import *

def remove_background_from_image(image_path,threshold):

	output_img_path = image_path.split('.')[0]+'_output1.'+image_path.split('.')[1]
	image_dir = os.path.dirname(image_path) + "/"
	#Removal of background using ImageMagick library
	os.system('convert -white-threshold '+str(threshold)+'% '+ image_path +' with '+ output_img_path)

	return output_img_path

def get_image_line_bounding_boxes(pathfile):
    src = cv2.imread(pathfile, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    lines_in_image = lsd(gray)
    return lines_in_image

def draw_lines_on_image(line_list,image_path):

	img = cv2.imread(image_path)
	for line in line_list :
		print(line)
		cv2.line(img,(int(line[0][0]),int(line[0][1])),(int(line[1][0]),int(line[1][1])),(0,255,0),2)
		cv2.imshow("test",img)
		cv2.waitKey(0)

def draw_lines_on_image1(line_list,image_path):
	img = cv2.imread(image_path)
	for line in line_list :
		print(line)
		cv2.line(img,(int(line[0]),int(line[1])),(int(line[2]),int(line[3])),(0,255,0),2)
		cv2.imshow("test1",img)
		cv2.waitKey(0)

def remove_extra_lines(y_axis, x_axis):

	max_x_axes = 0
	max_y_axes = 0
	x_len = 0
	y_len = 0

	for l in range(0,len(x_axis)):
		axes_len = x_axis[l][2] - x_axis[l][0]

		if axes_len > x_len:
			x_len = axes_len
			max_x_axes = l

	for l in range(0,len(y_axis)):
		axes_len = y_axis[l][3] - y_axis[l][1]

		if axes_len > y_len:
			y_len = axes_len
			max_y_axes = l
	
	return [y_axis[max_y_axes]],[x_axis[max_x_axes]]

def create_slope_list(tilted_lines):

	slope_list_neg = []
	slope_list_pos = []

	pos_slope_lines = []
	neg_slope_lines = []

	for line in tilted_lines:
		slope = (line[3]-line[1])/(line[2]-line[0])
		if slope < 0 :
			slope_list_neg.append(round(slope,1))
			neg_slope_lines.append(line)
		else:
			slope_list_pos.append(round(slope,1))
			pos_slope_lines.append(line)

	return neg_slope_lines,pos_slope_lines

def find_intersection(l1, l2):

	xdiff = (l1[0][0] - l1[1][0], l2[0][0] - l2[1][0])
	ydiff = (l1[0][1] - l1[1][1], l2[0][1] - l2[1][1])

	def det(a, b):
	    return a[0] * b[1] - a[1] * b[0]

	div = det(xdiff, ydiff)
	if div == 0:
		return "No","No"
	   # raise Exception('lines do not intersect')

	d = (det(*l1), det(*l2))
	x = det(d, xdiff) / div
	y = det(d, ydiff) / div

	return int(x), int(y)

def get_extended_lines(border_lines,tilted_lines,y_axis, x_axis):

	Y_max = y_axis[0][3]
	Y_min = y_axis[0][1]

	X_max = x_axis[0][2]
	X_min = x_axis[0][0]
	outer_list = []

	filtered_tilted_lines = []

	for line in tilted_lines:
		mid_X = int((line[2]+line[0])/2)
		mid_Y = int((line[3]+line[1])/2)

		if X_min < mid_X < X_max and Y_min < mid_Y < Y_max : 
			filtered_tilted_lines.append(line)

	for line1 in filtered_tilted_lines:
		result_list = []
		for l in range(0,len(border_lines)):
			x_int,y_int = find_intersection([(line1[0],line1[1]),(line1[2],line1[3])],border_lines[l])

			if l == 0 :
				if x_int ==  X_min and (Y_min <= y_int and y_int<= Y_max):
					result_list.append((int(x_int),int(y_int)))

			if l == 1 :
				if (X_min <= x_int and x_int <=X_max) and y_int == Y_min:
					result_list.append((int(x_int),int(y_int)))

			if l == 2 :
				if (Y_min <= y_int and y_int<= Y_max) and  x_int ==  X_max:
					result_list.append((int(x_int),int(y_int)))

			if l == 3:
				if (X_min <= x_int and x_int <=X_max) and y_int == Y_max:
					result_list.append((int(x_int),int(y_int)))

		outer_list.append(result_list)

	return outer_list

def remove_parallel_lines(outer_list):
	final_list = []
	unique_list = []

	for line in outer_list:
		if line in unique_list:
			continue
		else:
			unique_list.append(line)
		inner_list = []
		#pdb.set_trace()
		
		for line1 in outer_list:

			if line1 in unique_list:
				continue
			if abs(line[0][0]-line1[0][0]) < 25 and abs(line[0][1]-line1[0][1]) < 25 and abs(line[1][0]-line1[1][0]) < 25 and abs(line[1][1]-line1[1][1]) < 25:
				unique_list.append(line1)
				if line1 not in inner_list:
					inner_list.append(line1)
		if len(inner_list) == 0:
			inner_list.append(line)
		final_list.append(inner_list)
	#pdb.set_trace()
	final_coord = []
	for merged_line in final_list:
		x1_list = [i[0][0] for i in merged_line]
		y1_list = [i[0][1] for i in merged_line]
		x2_list = [i[1][0] for i in merged_line]
		y2_list = [i[1][1] for i in merged_line]
		final_coord.append([(int((sum(x1_list)/len(x1_list))),int((sum(y1_list)/len(y1_list)))),(int((sum(x2_list)/len(x2_list))),int((sum(y2_list)/len(y2_list))))])

	return final_coord

def get_axes_range(y_axis, x_axis, vertical_lines, horizontal_lines):

	X_origin = y_axis[0][0]
	Y_origin = x_axis[0][1]

	vertical_intersections_list = []

	left_y_intercepts_dict = {}
	right_y_intercepts_dict = {}

	above_x_intercepts_dict = {}
	below_x_intercepts_dict = {}

	x_intercepts_neg = 0
	x_intercepts_pos = 0
 
	for line in vertical_lines:
		
		x,y = find_intersection([(line[0],line[1]),(line[2],line[3])],[(x_axis[0][0],x_axis[0][1]),(x_axis[0][2],x_axis[0][3])])
		
		if x < X_origin and abs(X_origin-x) > 10 : 
			x_intercepts_neg+=1
			left_y_intercepts_dict[x_intercepts_neg] = (x,y)

		if x > X_origin and abs(X_origin-x) > 10 :
			x_intercepts_pos+=1
			right_y_intercepts_dict[x_intercepts_pos] = (x,y)

	y_intercepts_neg = 0
	y_intercepts_pos = 0

	for line in horizontal_lines:
		
		x,y = find_intersection([(line[0],line[1]),(line[2],line[3])],[(y_axis[0][0],y_axis[0][1]),(y_axis[0][2],y_axis[0][3])])
		
		if y < Y_origin and abs(Y_origin-y) > 10 : 
			y_intercepts_pos+=1
			above_x_intercepts_dict[y_intercepts_pos] = (x,y)

		if y > Y_origin and abs(Y_origin-y) > 10 :
			y_intercepts_neg+=1
			below_x_intercepts_dict[y_intercepts_neg] = (x,y)

	print(x_intercepts_neg, x_intercepts_pos, y_intercepts_pos, y_intercepts_neg)

	for xintercept in range(x_intercepts_neg,0,-1):
		left_y_intercepts_dict[-1*xintercept] = left_y_intercepts_dict[x_intercepts_neg-xintercept+1]
		del left_y_intercepts_dict[x_intercepts_neg-xintercept+1]

	for yintercept in range(1,y_intercepts_neg+1):
		below_x_intercepts_dict[-1*yintercept] = below_x_intercepts_dict[yintercept]
		del below_x_intercepts_dict[yintercept]

	#reverse the coords for Y above x axes:
	above_x_intercepts_dict_reversed = {}

	for yintercept in range(1,y_intercepts_pos+1):
		above_x_intercepts_dict_reversed[y_intercepts_pos-yintercept+1] = above_x_intercepts_dict[yintercept]

	# for yintercept in range(y_intercepts_neg,0,-1):
	# 	below_x_intercepts_dict[-1*yintercept] = below_x_intercepts_dict[y_intercepts_neg-yintercept+1]
	# 	del below_x_intercepts_dict[y_intercepts_neg-yintercept+1]

	print("X:", left_y_intercepts_dict)
	print("X:", right_y_intercepts_dict)
	print("Y:", below_x_intercepts_dict)
	print("Y:", above_x_intercepts_dict_reversed)

	x_axes_min = list(left_y_intercepts_dict.keys())
	x_axes_max = list(right_y_intercepts_dict.keys())
	y_axes_min = list(below_x_intercepts_dict.keys())
	y_axes_max = list(above_x_intercepts_dict_reversed.keys())

	x_range = (x_axes_min[0],x_axes_max[-1])
	y_range = (y_axes_min[-1],y_axes_max[0])

	print(y_range,x_range)

	return y_range, x_range, left_y_intercepts_dict, right_y_intercepts_dict, below_x_intercepts_dict, above_x_intercepts_dict_reversed

def number_to_words(num):
    words = ['One', 'Two', 'Three', 'Four', 'Five', 'Six']
    return str(words[num-1])

def number_to_words2(num):
    words = ['first', 'second', 'third', 'fourth']
    return str(words[num-1])

def get_intercept_with_XY_axes(x_axis,line,y_axis):

	temp = []

	X_axis = [(x_axis[0][0],x_axis[0][1]),(x_axis[0][2],x_axis[0][3])]
	Y_axis = [(y_axis[0][0],y_axis[0][1]),(y_axis[0][2],y_axis[0][3])]

	x,y = find_intersection(X_axis,line)

	if x_axis[0][0] < x <  x_axis[0][2]:
		print("Intersects X axes at :", x)
		temp.append(x)
	else:
		temp.append(9999)

	x,y = find_intersection(Y_axis,line)

	if y_axis[0][1] < x <  y_axis[0][3]:
		print("Intersects Y axes at :", y)
		temp.append(y)
	else:
		temp.append(9999)

	return temp[0],temp[1]

def map_value_to_intercept(x_intercept_point,y_intercept_point,left_y_intercepts_dict,right_y_intercepts_dict,below_x_intercepts_dict,above_x_intercepts_dict,x_origin,y_origin):

	result_X_val = 0
	result_Y_val = 0

	no_change_flag_X = 0
	no_change_flag_Y = 0

	if x_intercept_point < x_origin : 
		for intercept_value, intercept_coord in left_y_intercepts_dict.items():
			if abs(intercept_coord[0]-x_intercept_point) <= 5 :
				result_X_val = intercept_value
				no_change_flag_X = 1
				break

	if x_intercept_point > x_origin : 
		for intercept_value, intercept_coord in right_y_intercepts_dict.items():
			if abs(intercept_coord[0]-x_intercept_point) <= 5 :
				result_X_val = intercept_value
				no_change_flag_X = 1
				break

	if y_intercept_point < y_origin :
		for intercept_value, intercept_coord in above_x_intercepts_dict.items():
			if abs(intercept_coord[1]-y_intercept_point) <= 5 :
				result_Y_val = intercept_value
				no_change_flag_Y = 1
				break

	if y_intercept_point > y_origin :
		for intercept_value, intercept_coord in below_x_intercepts_dict.items():
			if abs(intercept_coord[1]-y_intercept_point) <= 5 :
				result_Y_val = intercept_value
				no_change_flag_Y = 1
				break

	print("map value",result_X_val,result_Y_val)

	return result_X_val,result_Y_val

def determine_start_end_quadrant(x_origin,y_origin,line):
	start_type = [1,2,3,4,'x','y']
	end_type = [1,2,3,4,'x','y']

	start_data = []
	end_data = []

	line_start_X,line_start_Y = line[0]
	line_end_X,line_end_Y = line[1]

	if abs(line_start_Y - y_origin) < 5 :
		start_data.append('X')

	if abs(line_start_X - x_origin) < 5 :
		start_data.append('Y')

	if abs(line_end_Y - y_origin) < 5 :
		end_data.append('X')

	if abs(line_end_X - x_origin) < 5 :
		end_data.append('Y')

	if len(start_data) == 0 :
		if line_start_X > x_origin and line_start_Y < y_origin :
			start_data.append(1)

		if line_start_X < x_origin and line_start_Y < y_origin :
			start_data.append(2)

		if line_start_X < x_origin and line_start_Y > y_origin :
			start_data.append(3)

		if line_start_X > x_origin and line_start_Y > y_origin :
			start_data.append(4)

	if len(end_data) == 0 :

		if line_end_X > x_origin and line_end_Y < y_origin :
			end_data.append(1)

		if line_end_X < x_origin and line_end_Y < y_origin :
			end_data.append(2)

		if line_end_X < x_origin and line_end_Y > y_origin :
			end_data.append(3)

		if line_end_X > x_origin and line_end_Y > y_origin :
			end_data.append(4)

	return start_data,end_data

def check_negative(coord):
	neg_str = ""

	if coord < 0 :
		return "negative "
	else:
		return ""

def get_line_wise_description(start_data,end_data,x_intercept_val,y_intercept_val,line_counter,line_startX,line_startY,line):

	line_desc = "The " + number_to_words2(line_counter) + " line"

	if start_data[0] == "X" :

		if x_intercept_val < 0 :
			line_desc = line_desc + " starts on the x axis at ( negative " + str(abs(x_intercept_val)) + ", 0 )"
		else:
			line_desc = line_desc + " starts on the x axis at ( " + str(abs(x_intercept_val)) + ", 0 )"

	if end_data[0] == "Y" :

		if y_intercept_val < 0 :
			line_desc = line_desc + " ends on the y axis at ( 0 , negative " + str(abs(y_intercept_val)) + " ). "
		else:
			line_desc = line_desc + " ends on the x axis at ( 0 , " + str(abs(y_intercept_val)) + " ). "

	if start_data[0] != "X" and start_data[0] != "Y" :
		line_desc = line_desc + " starts in the " +number_to_words2(start_data[0]) + " quadrant at ( " + check_negative(line_startX[0]) + str(abs(line_startX[0])) + ", " + check_negative(line_startX[1]) + str(abs(line_startX[1])) + " ), "

	#Add description for intersecting XY axes here

	if y_intercept_val != 9999 and x_intercept_val != 0:
	# if y_intercept_val != 9999 and y_intercept_val == 0 and x_intercept_val != 0:
		line_desc = line_desc + "crosses the x axis at ( " + check_negative(x_intercept_val) + str(abs(x_intercept_val)) + ", 0 ), "

	if x_intercept_val != 9999 and y_intercept_val !=0 :
	# if x_intercept_val != 9999 and x_intercept_val == 0 and y_intercept_val !=0 :
		line_desc = line_desc + "crosses the y axis at ( 0, " + check_negative(y_intercept_val) + str(abs(y_intercept_val)) + " ), "

	if x_intercept_val == 0 and y_intercept_val ==0 :
		line_desc = line_desc + "crosses the origin, "

	if end_data[0] != "X" and end_data[0] != "Y" :
		line_desc = line_desc + " ends in the " +number_to_words2(end_data[0]) + " quadrant at ( " + check_negative(line_startY[0]) + str(abs(line_startY[0])) + ", " + check_negative(line_startY[1]) + str(abs(line_startY[1])) + " ). "

	return line_desc

def process_line_graph(image_path):

	threshold = 70

	output_img_path = remove_background_from_image(image_path,threshold)
	#Run LSD here to find Axes 
	y_axis, x_axis,tilted_lines = get_hor_and_ver_merged_lines(output_img_path,"hor_ver")

	if len(y_axis) > 1 or len(x_axis) > 1 :
		y_axis, x_axis = remove_extra_lines(y_axis, x_axis)

	box_1 = [x_axis[0][0],y_axis[0][1]]
	box_2 = [x_axis[0][2],y_axis[0][1]]
	box_3 = [x_axis[0][2],y_axis[0][3]]
	box_4 = [x_axis[0][0],y_axis[0][3]]

	line1 = [(box_1[0],box_1[1]),(box_4[0],box_4[1])]
	line2 = [(box_1[0],box_1[1]),(box_2[0],box_2[1])]
	line3 = [(box_2[0],box_2[1]),(box_3[0],box_3[1])]
	line4 = [(box_4[0],box_4[1]),(box_3[0],box_3[1])]

	border_lines = [line1,line2,line3,line4]

	#Run merge LSD on original image
	vertical_lines, horizontal_lines, tilted_lines = get_hor_and_ver_merged_lines(image_path,"tilted")

	outer_list = get_extended_lines(border_lines,tilted_lines,y_axis, x_axis)
	main_lines = remove_parallel_lines(outer_list)

	# draw_lines_on_image(main_lines,image_path)

	#Find intersections - get axes range
	y_range, x_range, left_y_intercepts_dict, right_y_intercepts_dict, below_x_intercepts_dict, above_x_intercepts_dict = get_axes_range(y_axis, x_axis, vertical_lines, horizontal_lines)

	final_description = ""

	if len(main_lines) == 1:
		final_description = final_description + "A line is graphed on the x y coordinate plane. "
	if len(main_lines) == 2:
		slope_diff = ""
		#Check if intersecting or parallel
		slope1 = round((main_lines[0][1][1]-main_lines[0][0][1])/(main_lines[0][1][0]-main_lines[0][0][0]),1)
		slope2 = round((main_lines[1][1][1]-main_lines[1][0][1])/(main_lines[1][1][0]-main_lines[1][0][0]),1)

		if (slope1 < 0 and slope2 < 0) or (slope1 > 0 and slope2 > 0) :
			slope_diff = abs(slope1-slope2)

			#check intersection
			x_check,y_check = find_intersection(main_lines[0],main_lines[1])

			if x_check != "No" and y_check != "No" :
				#they are intesecting with very similar slope
				slope_diff = "intersecting"

			elif slope_diff < 1:
				slope_diff = "parallel"


		if (slope1 < 0 and slope2 > 0) or (slope1 < 0 and slope2 > 0) :
			slope_diff = "intersecting"
		
		if slope_diff == "parallel" : 
			final_description = final_description + "Two parallel lines are graphed on the x y coordinate plane. "
		else:
			final_description = final_description + "Two intersecting lines are graphed on the x y coordinate plane. "

	if len(main_lines) > 2: 
		final_description = final_description + str(number_to_words(len(main_lines))) + " lines are graphed on the x y coordinate plane. "

	final_description = final_description + "The x axis ranges from negative " + str(abs(x_range[0])) + " to " + str(abs(x_range[1])) + " with an interval of 1 unit. "

	final_description = final_description + "The y axis ranges from negative " + str(abs(y_range[0])) + " to " + str(abs(y_range[1])) + " with an interval of 1 unit. "

	X_axis = [(x_axis[0][0],x_axis[0][1]),(x_axis[0][2],x_axis[0][3])]
	Y_axis = [(y_axis[0][0],y_axis[0][1]),(y_axis[0][2],y_axis[0][3])]

	x_origin,y_origin = find_intersection(X_axis,Y_axis)

	line_counter = 1

	if len(main_lines) > 0:
		#If lines are there in graph
		add_x_desc_flag = 0
		add_y_desc_flag = 0

		for line in main_lines:

			x_intercept_point,y_intercept_point = get_intercept_with_XY_axes(x_axis,line,y_axis)

			if x_axis[0][0] < x_intercept_point < x_axis[0][2] + 5 :
				add_x_desc_flag = 1

			if y_axis[0][1] < y_intercept_point < y_axis[0][3] + 5 :
				add_y_desc_flag = 1

			#Case 1 : When line is intersecting both the axes
			if add_x_desc_flag == 1 and add_y_desc_flag == 1 :
				print("Case 1")

				#Start & End Quadrant/Axes
				start_data,end_data = determine_start_end_quadrant(x_origin,y_origin,line)

				#Intercepts with X & Y Axes
				x_intercept_val,y_intercept_val = map_value_to_intercept(x_intercept_point,y_intercept_point,left_y_intercepts_dict,right_y_intercepts_dict,below_x_intercepts_dict,above_x_intercepts_dict,x_origin,y_origin)

				line_startX = map_value_to_intercept(line[0][0],line[0][1],left_y_intercepts_dict,right_y_intercepts_dict,below_x_intercepts_dict,above_x_intercepts_dict,x_origin,y_origin)
				line_startY = map_value_to_intercept(line[1][0],line[1][1],left_y_intercepts_dict,right_y_intercepts_dict,below_x_intercepts_dict,above_x_intercepts_dict,x_origin,y_origin)

				line_desc = get_line_wise_description(start_data,end_data,x_intercept_val,y_intercept_val,line_counter,line_startX,line_startY,line)
				final_description = final_description + line_desc

				line_counter+=1

			#Case 2 : When line is intersecting either of the axes
			if (add_x_desc_flag == 1 and add_y_desc_flag == 0) or (add_x_desc_flag == 0 and add_y_desc_flag == 1) :
				print("Case 2")

				#Start & End Quadrant/Axes
				start_data,end_data = determine_start_end_quadrant(x_origin,y_origin,line)

				#Intercepts with X & Y Axes
				x_intercept_val,y_intercept_val = map_value_to_intercept(x_intercept_point,y_intercept_point,left_y_intercepts_dict,right_y_intercepts_dict,below_x_intercepts_dict,above_x_intercepts_dict,x_origin,y_origin)

				line_startX = map_value_to_intercept(line[0][0],line[0][1],left_y_intercepts_dict,right_y_intercepts_dict,below_x_intercepts_dict,above_x_intercepts_dict,x_origin,y_origin)
				line_startY = map_value_to_intercept(line[1][0],line[1][1],left_y_intercepts_dict,right_y_intercepts_dict,below_x_intercepts_dict,above_x_intercepts_dict,x_origin,y_origin)

				line_desc = get_line_wise_description(start_data,end_data,x_intercept_val,y_intercept_val,line_counter,line_startX,line_startY,line)
				final_description = final_description + line_desc

				line_counter+=1


	if len(main_lines) == 2 and slope_diff != "parallel" :

		intersect_pt_x,intersect_pt_y = find_intersection(main_lines[0],main_lines[1])
		intersect_pt_x,intersect_pt_y = map_value_to_intercept(intersect_pt_x,intersect_pt_y,left_y_intercepts_dict,right_y_intercepts_dict,below_x_intercepts_dict,above_x_intercepts_dict,x_origin,y_origin)

		final_description = final_description + "The two lines intersect at ( " + check_negative(intersect_pt_x) + str(abs(intersect_pt_x)) + ", " + check_negative(intersect_pt_y) + str(abs(intersect_pt_y)) + " )."

	return final_description

def main():

	image_list = glob.glob('/Users/CE/Desktop/Pearson_Demo/Automated/*.png')
	final_desc_list = []

	failed_list = []

	# try:
	for image in image_list:
		print("Starting for image: ", image)

		final_description = process_line_graph('/Users/CE/Desktop/Pearson_Demo/Automated/Martin-Gay_13.5example2.PNG')

		print(final_description)
		pdb.set_trace()

		final_desc_list.append([image,final_description])
	# except :
	# 	failed_list.append(image)

	pdb.set_trace()
main()