// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MaterialRegistry
 * @notice 学习资料注册、查询、下载合约
 * @dev 链上仅存哈希/SimHash/元数据，禁止存文件本体
 *
 * 核心流程:
 *   register → 存元数据 + mint 20 EDU 给上传者
 *   download → transferFrom 下载者 → 上传者（需提前 approve）
 */

interface IEduToken {
    function mint(address to, uint256 amount) external;
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract MaterialRegistry {

    // ========== 数据结构 ==========

    struct Material {
        string   id;            // 资料唯一标识（后端生成）
        string   name;          // 资料名称
        string   course;        // 所属课程
        address  uploader;      // 上传者地址
        bytes32  sha256Hash;    // 文件 SHA-256 哈希
        uint256  simHash;       // 内容 SimHash 指纹
        uint32   textLength;    // 提取文本长度
        uint8    policyType;    // 访问策略类型 (0=公开, 1=同课程, 2=指定用户)
        string   policyValue;   // 策略参数（如课程编号、用户列表 JSON）
        uint256  price;         // 下载价格 (EDU)
        uint32   version;       // 版本号
        bool     deleted;       // 软删除标记
        uint256  timestamp;     // 注册时间戳
    }

    // ========== 状态变量 ==========

    IEduToken public eduToken;
    address   public owner;

    uint256 public constant UPLOAD_REWARD = 20;

    // materialId => Material
    mapping(string => Material) private materials;
    // 所有资料 ID 列表（用于遍历）
    string[] public materialIds;
    // sha256Hash => materialId（用于查重）
    mapping(bytes32 => string) public hashToMaterialId;

    // ========== Events ==========

    event MaterialRegistered(
        string indexed id,
        string   name,
        address  indexed uploader,
        bytes32  sha256Hash,
        uint256  simHash,
        uint256  price,
        uint256  timestamp
    );

    event MaterialDownloaded(
        string  indexed materialId,
        address indexed downloader,
        address indexed uploader,
        uint256 price,
        uint256 timestamp
    );

    event MaterialUpdated(
        string indexed id,
        uint32 newVersion,
        bytes32 newSha256Hash,
        uint256 newSimHash,
        uint256 timestamp
    );

    event MaterialDeleted(
        string indexed id,
        address indexed caller,
        uint256 timestamp
    );

    // ========== Modifiers ==========

    modifier onlyOwner() {
        require(msg.sender == owner, "MaterialRegistry: caller is not owner");
        _;
    }

    // ========== Constructor ==========

    /**
     * @param _tokenAddress EduToken 合约地址
     */
    constructor(address _tokenAddress) {
        require(_tokenAddress != address(0), "MaterialRegistry: zero token address");
        eduToken = IEduToken(_tokenAddress);
        owner = msg.sender;
    }

    // ========== 核心函数 ==========

    /**
     * @notice 注册新资料，铸造 20 EDU 奖励给上传者
     * @dev 由后端通过 owner 账户调用
     */
    function register(
        string calldata _id,
        string calldata _name,
        string calldata _course,
        address         _uploader,
        bytes32         _sha256Hash,
        uint256         _simHash,
        uint32          _textLength,
        uint8           _policyType,
        string calldata _policyValue,
        uint256         _price
    ) external onlyOwner {
        // 检查资料 ID 不重复
        require(bytes(materials[_id].id).length == 0, "MaterialRegistry: id already exists");
        // 检查 SHA-256 不重复（防止完全相同的文件重复上传）
        require(bytes(hashToMaterialId[_sha256Hash]).length == 0, "MaterialRegistry: file hash already registered");

        Material memory m = Material({
            id:          _id,
            name:        _name,
            course:      _course,
            uploader:    _uploader,
            sha256Hash:  _sha256Hash,
            simHash:     _simHash,
            textLength:  _textLength,
            policyType:  _policyType,
            policyValue: _policyValue,
            price:       _price,
            version:     1,
            deleted:     false,
            timestamp:   block.timestamp
        });

        materials[_id] = m;
        materialIds.push(_id);
        hashToMaterialId[_sha256Hash] = _id;

        // 铸造上传奖励
        eduToken.mint(_uploader, UPLOAD_REWARD);

        emit MaterialRegistered(_id, _name, _uploader, _sha256Hash, _simHash, _price, block.timestamp);
    }

    /**
     * @notice 查询资料详情
     * @param _id 资料 ID
     * @return 资料结构体
     */
    function query(string calldata _id) external view returns (Material memory) {
        require(bytes(materials[_id].id).length > 0, "MaterialRegistry: material not found");
        return materials[_id];
    }

    /**
     * @notice 版本更新（追加新版本的哈希和指纹）
     */
    function update(
        string calldata _id,
        bytes32         _newSha256Hash,
        uint256         _newSimHash,
        uint32          _newTextLength
    ) external onlyOwner {
        Material storage m = materials[_id];
        require(bytes(m.id).length > 0, "MaterialRegistry: material not found");
        require(!m.deleted, "MaterialRegistry: material is deleted");

        // 更新哈希映射
        delete hashToMaterialId[m.sha256Hash];
        hashToMaterialId[_newSha256Hash] = _id;

        m.sha256Hash = _newSha256Hash;
        m.simHash    = _newSimHash;
        m.textLength = _newTextLength;
        m.version   += 1;
        m.timestamp  = block.timestamp;

        emit MaterialUpdated(_id, m.version, _newSha256Hash, _newSimHash, block.timestamp);
    }

    /**
     * @notice 下载资料，从下载者向上传者转移通证
     * @dev 下载者需提前调用 EduToken.approve(MaterialRegistry地址, price)
     * @param _materialId 资料 ID
     * @param _downloader 下载者地址
     */
    function download(string calldata _materialId, address _downloader) external onlyOwner {
        Material storage m = materials[_materialId];
        require(bytes(m.id).length > 0, "MaterialRegistry: material not found");
        require(!m.deleted, "MaterialRegistry: material is deleted");
        require(_downloader != m.uploader, "MaterialRegistry: cannot download own material");

        if (m.price > 0) {
            // 检查余额
            require(
                eduToken.balanceOf(_downloader) >= m.price,
                "MaterialRegistry: insufficient EDU balance"
            );
            // 转移通证：下载者 → 上传者
            bool success = eduToken.transferFrom(_downloader, m.uploader, m.price);
            require(success, "MaterialRegistry: token transfer failed");
        }

        emit MaterialDownloaded(_materialId, _downloader, m.uploader, m.price, block.timestamp);
    }

    /**
     * @notice 软删除资料
     * @param _id     资料 ID
     * @param _caller 调用者地址（后端传入，权限在后端校验）
     */
    function softDelete(string calldata _id, address _caller) external onlyOwner {
        Material storage m = materials[_id];
        require(bytes(m.id).length > 0, "MaterialRegistry: material not found");
        require(!m.deleted, "MaterialRegistry: already deleted");
        require(_caller == m.uploader, "MaterialRegistry: only uploader can delete");

        m.deleted = true;

        emit MaterialDeleted(_id, _caller, block.timestamp);
    }

    // ========== 辅助查询 ==========

    /**
     * @notice 获取资料总数
     */
    function getMaterialCount() external view returns (uint256) {
        return materialIds.length;
    }

    /**
     * @notice 通过 SHA-256 哈希查询资料 ID（用于查重）
     */
    function getMaterialByHash(bytes32 _hash) external view returns (string memory) {
        return hashToMaterialId[_hash];
    }
}
