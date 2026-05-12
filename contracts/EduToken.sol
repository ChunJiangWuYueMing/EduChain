// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title EduToken
 * @notice EduChain 平台通证，整数积分制（decimals = 0）
 * @dev 仅 owner（部署者 / MaterialRegistry）可铸造
 *
 * 通证经济:
 *   注册奖励   +100 (后端调用 mint)
 *   上传资料   +20  (MaterialRegistry.register 内部调用)
 *   下载资料   下载者 → 上传者 transferFrom (MaterialRegistry.download 内部调用)
 *   抄袭扣罚   -50  (后端调用 burn, 预留)
 */
contract EduToken is ERC20, Ownable {

    // ========== State ==========
    mapping(address => bool) public authorizedMinters;

    // ========== Events ==========
    event TokensMinted(address indexed to, uint256 amount, string reason);
    event TokensBurned(address indexed from, uint256 amount, string reason);
    event MinterAuthorized(address indexed minter);
    event MinterRevoked(address indexed minter);

    // ========== Modifiers ==========
    modifier onlyMinter() {
        require(
            msg.sender == owner() || authorizedMinters[msg.sender],
            "EduToken: caller is not owner or authorized minter"
        );
        _;
    }

    constructor() ERC20("EduToken", "EDU") Ownable(msg.sender) {}

    /**
     * @notice 授权地址铸造权限（部署 MaterialRegistry 后调用）
     */
    function authorizeMinter(address minter) external onlyOwner {
        authorizedMinters[minter] = true;
        emit MinterAuthorized(minter);
    }

    /**
     * @notice 撤销铸造权限
     */
    function revokeMinter(address minter) external onlyOwner {
        authorizedMinters[minter] = false;
        emit MinterRevoked(minter);
    }

    /**
     * @notice 返回 0，表示整数积分，无小数位
     */
    function decimals() public pure override returns (uint8) {
        return 0;
    }

    /**
     * @notice 铸造通证（仅 owner）
     * @param to    接收地址
     * @param amount 数量
     */
    function mint(address to, uint256 amount) external onlyMinter {
        _mint(to, amount);
        emit TokensMinted(to, amount, "mint");
    }

    /**
     * @notice 带原因的铸造（方便日志追溯）
     * @param to     接收地址
     * @param amount 数量
     * @param reason 原因（如 "register", "upload"）
     */
    function mintWithReason(address to, uint256 amount, string calldata reason) external onlyMinter {
        _mint(to, amount);
        emit TokensMinted(to, amount, reason);
    }

    /**
     * @notice 销毁通证（仅 owner，用于抄袭扣罚等）
     * @param from   被扣地址
     * @param amount 数量
     * @param reason 原因
     */
    function burnFrom(address from, uint256 amount, string calldata reason) external onlyOwner {
        _burn(from, amount);
        emit TokensBurned(from, amount, reason);
    }
}
