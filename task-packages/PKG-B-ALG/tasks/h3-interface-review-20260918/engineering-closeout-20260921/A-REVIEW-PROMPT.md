# 给A的集中复核请求

请复核本仓库 `task/member-b-h3-engineering-closeout-20260921`，准确候选SHA见本目录DELIVERY发布补记（不要只按可移动分支头审）。包为 `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/`，入口README。

基线cf026cf29518488f8c7275b825f3487a8d892f80；已核对新增e473824仅声学离线批准。已关闭fe67547/b5913e5/349501c/f879/a7f70c5/268e526保持原范围，不全量复跑、不重派E01～03。

申请仅批准：本子目录的B离线候选、检查器、异常夹具、合同/预算资料。新增CORDIC共同左移与规范角度未替换FG；旧小向量失败保留，新1215向量误差界≤1 Q8码，新的S28内部界须单独审。轨迹checker为B准备材料，非生产实现；请重点检查独立expected_units不能由DUT削弱、背压payload保持、晚错/reset顺序与实际采样时间区分。

复现：Python3.12+NumPy2.3.5，在准确提交根执行 `python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/run_all.py --repo . --out <不存在的新目录>`。再执行同目录 `check_delivery.py --repo . --out <新的检查结果.json>`，核对run05源码/输出哈希和旧FG/D依赖。不改冻结结果吸收差异。测试/未测见README；完整FFT/IFFT、AMD、RTL、Vivado/Vitis、板测与声学研究本轮未运行。

请一次给出：原/归一化CORDIC是否需要单独生产profile；8前视/17历史与串行pending/最多20ms平滑回mono能否接受；session/TTL/available统一时基与硬停分界；ROM部署与有限服务证据下一步。reference25保留，portable Q30与AMD24黄金独立，107496B/202816B/552960B不混加，缺服务上界继续REALTIME_BLOCKED。不要将限定软件批准写成生产接口、完整H3或实时冻结。

目标活动路径仍本任务包候选目录；新实现由A独立审，B不自审自合。未选择实际one/Vitis工程、未导入RTL/IP或改A/C文件。无可立即删除分支/副本；待审分支及其独有证据必须保留。其他声学对话不在本复核范围。
