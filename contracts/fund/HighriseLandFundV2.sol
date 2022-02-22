// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import "@openzeppelin/contracts/utils/introspection/ERC165Checker.sol";

import "../../interfaces/IHighriseLand.sol";

contract HighriseLandFundV2 {
    using ERC165Checker for address;

    event FundLandEvent(
        address indexed sender,
        uint256 fundAmount,
        string reservationId
    );

    enum FundState {
        ENABLED,
        DISABLED
    }

    address public owner;
    address landContract;

    // mapping to store which address deposited how much ETH
    mapping(address => uint256) public addressToAmountFunded;
    // token price in wei
    uint256 public landTokenPrice;
    FundState fundState;

    constructor(uint256 _landTokenPrice, address _landContract) {
        require(_landContract.supportsInterface(type(IHighriseLand).interfaceId), "IS_NOT_HIGHRISE_LAND_CONTRACT");
        owner = msg.sender;
        landTokenPrice = _landTokenPrice;
        fundState = FundState.DISABLED;
        landContract = _landContract;
    }

    modifier validAmount() {
        require(
            msg.value >= landTokenPrice,
            "Not enough ETH to pay for tokens"
        );
        _;
    }

    modifier enabled() {
        require(
            fundState == FundState.ENABLED,
            "Contract not enabled for funding"
        );
        _;
    }

    function fund(string calldata reservationId)
        public
        payable
        enabled
        validAmount
    {
        addressToAmountFunded[msg.sender] += msg.value;
        (IHighriseLand(landContract)).mint(msg.sender, 1);
        emit FundLandEvent(msg.sender, msg.value, reservationId);
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
}
