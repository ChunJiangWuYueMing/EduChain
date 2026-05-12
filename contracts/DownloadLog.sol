// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title DownloadLog
 * @notice 下载日志合约，记录每次下载行为供审计查询
 */
contract DownloadLog {

    // ========== 数据结构 ==========

    struct DownloadRecord {
        string   materialId;    // 资料 ID
        address  downloader;    // 下载者地址
        address  uploader;      // 上传者地址
        uint256  price;         // 扣费金额
        bytes32  fileHash;      // 下载时文件的 SHA-256（完整性凭证）
        uint256  timestamp;     // 下载时间
    }

    // ========== 状态变量 ==========

    address public owner;

    DownloadRecord[] public allRecords;

    // materialId => record indices
    mapping(string => uint256[]) private materialRecords;
    // downloader => record indices
    mapping(address => uint256[]) private downloaderRecords;

    // ========== Events ==========

    event DownloadRecorded(
        uint256 indexed recordIndex,
        string   materialId,
        address  indexed downloader,
        address  indexed uploader,
        uint256  price,
        uint256  timestamp
    );

    // ========== Modifiers ==========

    modifier onlyOwner() {
        require(msg.sender == owner, "DownloadLog: caller is not owner");
        _;
    }

    // ========== Constructor ==========

    constructor() {
        owner = msg.sender;
    }

    // ========== 核心函数 ==========

    /**
     * @notice 记录一次下载
     */
    function recordDownload(
        string calldata _materialId,
        address         _downloader,
        address         _uploader,
        uint256         _price,
        bytes32         _fileHash
    ) external onlyOwner {
        DownloadRecord memory record = DownloadRecord({
            materialId: _materialId,
            downloader: _downloader,
            uploader:   _uploader,
            price:      _price,
            fileHash:   _fileHash,
            timestamp:  block.timestamp
        });

        uint256 index = allRecords.length;
        allRecords.push(record);

        materialRecords[_materialId].push(index);
        downloaderRecords[_downloader].push(index);

        emit DownloadRecorded(index, _materialId, _downloader, _uploader, _price, block.timestamp);
    }

    // ========== 查询函数 ==========

    /**
     * @notice 按资料 ID 查询下载记录
     */
    function queryByMaterial(string calldata _materialId) external view returns (DownloadRecord[] memory) {
        uint256[] storage indices = materialRecords[_materialId];
        DownloadRecord[] memory records = new DownloadRecord[](indices.length);
        for (uint256 i = 0; i < indices.length; i++) {
            records[i] = allRecords[indices[i]];
        }
        return records;
    }

    /**
     * @notice 按下载者地址查询下载记录
     */
    function queryByDownloader(address _downloader) external view returns (DownloadRecord[] memory) {
        uint256[] storage indices = downloaderRecords[_downloader];
        DownloadRecord[] memory records = new DownloadRecord[](indices.length);
        for (uint256 i = 0; i < indices.length; i++) {
            records[i] = allRecords[indices[i]];
        }
        return records;
    }

    /**
     * @notice 获取总下载记录数
     */
    function getRecordCount() external view returns (uint256) {
        return allRecords.length;
    }
}
