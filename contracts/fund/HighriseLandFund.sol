// SPDX-License-Identifier: MIT
pragma solidity ^0.8.12;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/introspection/ERC165Checker.sol";

import "../../interfaces/IHighriseLand.sol";

contract HighriseLandFund {
    using ERC165Checker for address;
    using ECDSA for bytes32;

    event FundLandEvent(address indexed sender, uint256 fundAmount);

    enum FundState {
        ENABLED,
        DISABLED
    }

    address public owner;
    address landContract;

    // mapping to store which address deposited how much ETH
    mapping(address => uint256) public addressToAmountFunded;
    FundState fundState;

    constructor(address _landContract) {
        require(
            _landContract.supportsInterface(type(IHighriseLand).interfaceId),
            "IS_NOT_HIGHRISE_LAND_CONTRACT"
        );
        owner = msg.sender;
        fundState = FundState.DISABLED;
        landContract = _landContract;
    }

    modifier enabled() {
        require(
            fundState == FundState.ENABLED,
            "Contract not enabled for funding"
        );
        _;
    }

    function fund(bytes memory data, bytes memory signature)
        public
        payable
        enabled
    {
        require(_verify(keccak256(data), signature, owner));
        (uint256 tokenId, uint256 expiry, uint256 cost) = abi.decode(
            abi.encodePacked(data),
            (uint256, uint256, uint256)
        );
        require(expiry > block.timestamp, "Reservation expired");
        require(msg.value >= cost);
        addressToAmountFunded[msg.sender] += msg.value;
        (IHighriseLand(landContract)).mint(msg.sender, tokenId);
        emit FundLandEvent(msg.sender, msg.value);
    }

    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    function enable() public onlyOwner {
        fundState = FundState.ENABLED;
    }

    function disable() public onlyOwner {
        fundState = FundState.DISABLED;
    }

    modifier disabled() {
        require(
            fundState == FundState.DISABLED,
            "Disable contract before withdrawing"
        );
        _;
    }

    function withdraw() public onlyOwner disabled {
        payable(msg.sender).transfer(address(this).balance);
    }

    function _verify(
        bytes32 data,
        bytes memory signature,
        address account
    ) internal pure returns (bool) {
        return data.recover(signature) == account;
    }
}
