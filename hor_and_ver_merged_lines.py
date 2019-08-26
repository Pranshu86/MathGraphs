import ocrbox
from pylsd.lsd import lsd
import cv2
from os import listdir, path
import numpy as np
import pdb
from PIL import Image

def get_word_bounding_boxes( micro_soft_ocr):
    word_bounding_box_info = []    
    for text_info in micro_soft_ocr:
        for word_info in text_info['words']:
            word_bounding_box_info.append(word_info)
    return word_bounding_box_info

def get_text_bounding_boxes(micro_soft_ocr):
   text_bounding_box_info = []
   for text_info in micro_soft_ocr:
       bounding_box_info = {}
       bounding_box_info['boundingBox'] = text_info['boundingBox']
       bounding_box_info['text'] = text_info['text']
       text_bounding_box_info.append(bounding_box_info)
   return text_bounding_box_info

def get_row_wise_text_info(word_bounding_boxes):
    
    if len(word_bounding_boxes) == 0:
        return word_bounding_boxes
    else:
        row_wise_text_list = []
        sort_text_list = sorted(word_bounding_boxes, key=lambda text_info: text_info['boundingBox'][7])
        index = 0
        row_info = []
        while index < len(word_bounding_boxes):
            if (index+1) == len(word_bounding_boxes):
                row_info.append(sort_text_list[index])
                #sort_row_info = sorted(row_info, key=lambda text_info: text_info['boundingBox'][0])
                sort_row_info = row_info
                row_wise_text_list.append(sort_row_info)
                break
            if len(row_info) == 0 :
                row_info.append(sort_text_list[index])
                index = index + 1
            elif len(row_info) > 0 and sort_text_list[index]['boundingBox'][7] - row_info[0]['boundingBox'][7]  <= 14:
                row_info.append(sort_text_list[index])
                index = index + 1
            else:
                sort_row_info = row_info
                row_wise_text_list.append(sort_row_info)
                row_info = []
        return row_wise_text_list

def getting_horizontal_vertical_lines_values_from_lsd(ver_lines):

    horizontal_lines_values = []
    vertical_line_values = []
    tilted_lines = []

    for line in range(0,len(ver_lines)):
        if(abs(int(ver_lines[line][1]) - int(ver_lines[line][3])) < 3):        
            horizontal_lines_values.append(ver_lines[line])
        elif(abs(int(ver_lines[line][0]) - int(ver_lines[line][2]) ) < 3):
            vertical_line_values.append(ver_lines[line])
        else:
            tilted_lines.append(ver_lines[line])

    horizontal_lines_values  = sorted(horizontal_lines_values, key=lambda i: (int(i[1])))
    vertical_line_values = sorted(vertical_line_values, key=lambda i: (int(i[1])))
    return horizontal_lines_values,vertical_line_values,tilted_lines

def remove_lines_inside_text_box(lines_bounding_boxes,word_bounding_boxes):

    
    remove_line_cord = []
    remove_line_cord_copy = []
    line_coord_list = []
    for line_coord in lines_bounding_boxes:
        line_coord_list.append((int(line_coord[0]),int(line_coord[1]),int(line_coord[2]),int(line_coord[3])))
   
    for word_bounding_box in word_bounding_boxes:
        word_coord = word_bounding_box['boundingBox']
        word_x3 = max(word_coord[0],word_coord[2],word_coord[4],word_coord[6])
        word_x1 = min(word_coord[0],word_coord[2],word_coord[4],word_coord[6])
        word_y1 = min(word_coord[1],word_coord[3],word_coord[5],word_coord[7])
        word_y3 = max(word_coord[1],word_coord[3],word_coord[5],word_coord[7])

        for line_coord in line_coord_list:
            if (int(line_coord[3])-int(line_coord[1])) > 50:
                continue
            line_x1,line_y1 = int(abs(line_coord[0]+line_coord[2])/2),int(abs(line_coord[1]+line_coord[3])/2)
            if word_x1 > word_x3:
                word_x1,word_x3 = word_x3,word_x1
            if word_y1 > word_y3:
                word_y1,word_y3 = word_y3,word_y1
            if (line_x1  in range(word_x1-1 ,word_x3+1)) and (line_y1 in range(word_y1-1, word_y3+1)):
                remove_line_cord.append(line_coord)
    res_line_coord = set(line_coord_list)^set(remove_line_cord)
    res_line_coord = list(res_line_coord)    
    return res_line_coord

def group_vertical_lines(hori_lines):
    horizontal_group_list = []
    check_list = []
    lines = []
    for i in range(0,len(hori_lines)):
        inner_list = []
        if hori_lines[i] in check_list:
            continue
        inner_list.append(hori_lines[i])
        check_list.append(hori_lines[i])
        for j in range(i+1,len(hori_lines)):            
            if (hori_lines[i][0] == hori_lines[j][0]) or abs(hori_lines[i][0] - hori_lines[j][0]) <= 10:
                check_list.append(hori_lines[j])
                inner_list.append(hori_lines[j])
        horizontal_group_list.append(inner_list)
    for i in range(0,len(horizontal_group_list)):
        horizontal_group_list[i] = sorted(horizontal_group_list[i],key=lambda x : x[1])
        #print(horizontal_group_list[i][0], horizontal_group_list[i][-1])
        lines.append(horizontal_group_list[i][0])
    lines = sorted(lines , key = lambda x: x[0])
    return horizontal_group_list,lines

def get_vertical_merging_lines(vertical_grouping_list):

    ver_merg_line_list = []
    for ver_line_list in vertical_grouping_list:
        x_index = ver_line_list[0][0]
        ver_line_min_index = sorted(ver_line_list,key=lambda x : x[1])
        ver_line_max_index = sorted(ver_line_list,key=lambda x : x[3])
        merge_line_coord = [x_index, ver_line_min_index[0][1], x_index, ver_line_max_index[-1][3]]
        ver_merg_line_list.append(merge_line_coord)
    ver_merg_line_list = sorted(ver_merg_line_list,key=lambda x : x[0])
    return ver_merg_line_list


def group_horizantal_lines(hori_lines):
    horizontal_group_list = []
    check_list = []
    lines = []
    for i in range(0,len(hori_lines)):
        inner_list = []
        if hori_lines[i] in check_list:
            continue
        inner_list.append(hori_lines[i])
        check_list.append(hori_lines[i])
        for j in range(i+1,len(hori_lines)):            
            if (hori_lines[i][1] == hori_lines[j][1]) or abs(hori_lines[i][1] - hori_lines[j][1]) <= 8:
                check_list.append(hori_lines[j])
                inner_list.append(hori_lines[j])
        horizontal_group_list.append(inner_list)
    return horizontal_group_list

def convert_lines_df_to_list(lines_bounding_boxes):
    line_coord_list = []
    for line_coord in lines_bounding_boxes:
        if int(line_coord[0]) > int(line_coord[2]):
            line_coord = (int(line_coord[2]),int(line_coord[1]),int(line_coord[0]),int(line_coord[3]))
        if int(line_coord[1]) > int(line_coord[3]):
            line_coord = (int(line_coord[0]),int(line_coord[3]),int(line_coord[2]),int(line_coord[1]))
        else:
            line_coord = (int(line_coord[0]),int(line_coord[1]),int(line_coord[2]),int(line_coord[3]))

        line_coord_list.append(line_coord)
    return line_coord_list

def convert_lines_df_to_list1(lines_bounding_boxes):
    line_coord_list = []
    for line_coord in lines_bounding_boxes:
        line_coord_list.append(line_coord)
    return line_coord_list

def get_horizantal_merging_lines(horizontal_grouping_list):

    hor_merg_line_list = []
    for horizontal_line_list in horizontal_grouping_list:
        y_index = horizontal_line_list[0][1]
        hor_line_min_index = sorted(horizontal_line_list,key=lambda x : x[0])
        hor_line_max_index = sorted(horizontal_line_list,key=lambda x : x[2])
        merge_line_coord = [hor_line_min_index[0][0],y_index, hor_line_max_index[-1][2], y_index]
        hor_merg_line_list.append(merge_line_coord)
    return hor_merg_line_list

def get_hor_and_ver_merged_lines(image_path,line_type):
    micro_soft_ocr = ocrbox.result_microsoft_api(image_path)
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    gray_clr_obj = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lines_arr = lsd(gray_clr_obj)
    word_bounding_boxes = get_word_bounding_boxes(micro_soft_ocr)
    text_bounding_boxes = get_text_bounding_boxes(micro_soft_ocr)

    if line_type != "tilted" : 
        line_coord_list=convert_lines_df_to_list(lines_arr)
    else:
        line_coord_list=convert_lines_df_to_list1(lines_arr)

    filter_line_coord_list = remove_lines_inside_text_box(line_coord_list,word_bounding_boxes)
    horizontal_values,vertical_values,tilted_lines = getting_horizontal_vertical_lines_values_from_lsd(filter_line_coord_list)   

    vertical_grouping_list,ver_grouping_lines = group_vertical_lines(vertical_values)
    final_table_vcoordinates = get_vertical_merging_lines(vertical_grouping_list)
    horizontal_grouping_list = group_horizantal_lines(horizontal_values)
    final_table_hcoordinates = get_horizantal_merging_lines(horizontal_grouping_list)

    return final_table_vcoordinates, final_table_hcoordinates,tilted_lines

# image_path = "/Users/prasanthpotnuru/Downloads/3_table_2/005.png"
# get_hor_and_ver_merged_lines(image_path)