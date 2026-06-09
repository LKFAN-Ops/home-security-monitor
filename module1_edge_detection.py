#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 模块一：边缘检测与车辆轮廓绘制
import cv2
import numpy as np

img = cv2.imread("data/4.jpg")
if img is None:
    print("图片读取失败，请检查路径是否正确！")
else:
    # 2. 图像预处理：灰度化 + 高斯模糊
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. Canny边缘检测
    edges = cv2.Canny(blur, 80, 250)

    # 4. 轮廓提取
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 5. 绘制轮廓
    img_contour = cv2.drawContours(img.copy(), contours, -1, (0, 255, 0), 2)

    # 6. 创建可自适应调节大小的窗口
    cv2.namedWindow("原始图片",     cv2.WINDOW_NORMAL)  # WINDOW_NORMAL 允许拖拽调整大小
    cv2.namedWindow("Canny边缘检测", cv2.WINDOW_NORMAL)
    cv2.namedWindow("车辆轮廓绘制", cv2.WINDOW_NORMAL)

    # 设置初始窗口大小（可自行修改）
    cv2.resizeWindow("原始图片",     800, 600)
    cv2.resizeWindow("Canny边缘检测", 800, 600)
    cv2.resizeWindow("车辆轮廓绘制", 800, 600)

    # 7. 显示结果
    cv2.imshow("原始图片",     img)
    cv2.imshow("Canny边缘检测", edges)
    cv2.imshow("车辆轮廓绘制", img_contour)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

#---------Sobel算法------------
# # !/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # 模块一：边缘检测与车辆轮廓绘制
# import cv2  # 导入opencv库（图像处理核心）
# import numpy as np  # 导入numpy库（数据处理）
#
# # 1. 读取车辆图片（替换为自己的图片路径，注意路径不要有中文）
# img = cv2.imread("data/4.jpg")  # data文件夹下的car1.jpg图片
# # 判读图片是否读取成功（路径错误是常见问题）
# if img is None:
#     print("图片读取失败，请检查路径是否正确！")
# else:
#     # 2. 图像预处理：灰度化 + 高斯模糊
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 灰度化，转为黑白图片
#     blur = cv2.GaussianBlur(gray, (5, 5), 0)  # 高斯模糊，去除噪声（5,5是模糊核，0是标准差）
#
#     # ===================== 已替换为 Sobel 边缘检测 =====================
#     # Sobel X 方向梯度（检测垂直边缘）
#     sobel_x = cv2.Sobel(blur, cv2.CV_64F, 1, 0, ksize=3)
#     # Sobel Y 方向梯度（检测水平边缘）
#     sobel_y = cv2.Sobel(blur, cv2.CV_64F, 0, 1, ksize=3)
#
#     # 取绝对值并合并 X、Y 方向梯度
#     abs_sobel_x = cv2.convertScaleAbs(sobel_x)
#     abs_sobel_y = cv2.convertScaleAbs(sobel_y)
#     edges = cv2.addWeighted(abs_sobel_x, 0.5, abs_sobel_y, 0.5, 0)
#     # =================================================================
#
#     # 4. 轮廓提取（从边缘检测结果中提取车辆轮廓）
#     # RETR_EXTERNAL：只提取最外层轮廓；CHAIN_APPROX_SIMPLE：简化轮廓，减少点的数量
#     contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#
#     # 5. 绘制轮廓（在原始图片上绘制轮廓，便于对比）
#     # 第一个参数：原始图片，第二个参数：轮廓列表，第三个参数：-1表示绘制所有轮廓，第四个参数：颜色（BGR，绿色），第五个参数：线条粗细
#     img_contour = cv2.drawContours(img.copy(), contours, -1, (0, 255, 0), 2)
#
#     # 6. 显示结果（弹出窗口，展示原始图片、边缘检测结果、轮廓绘制结果）
#     cv2.imshow("原始图片", img)
#     cv2.imshow("Sobel边缘检测", edges)
#     cv2.imshow("车辆轮廓绘制", img_contour)
#
#     # 等待按键（0表示无限等待，按任意键关闭窗口）
#     cv2.waitKey(0)
#     # 关闭所有窗口（避免占用内存）
#     cv2.destroyAllWindows()