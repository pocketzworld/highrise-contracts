// SPDX-License-Identifier: MIT
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "./HighriseLand.sol";

pragma solidity ^0.8.11;

contract HighriseLandFund {
    using ECDSA for bytes32;

    address public owner;
    address public landContract;

    // mapping to store which address deposited how much ETH
    mapping(address => uint256) public addressToAmountFunded;

    // token price in wei
    uint256 public landTokenPrice;

    enum FundState {
        ENABLED,
        DISABLED
    }

    FundState fundState;

    event FundLandEvent(
        address indexed sender,
        uint256 fundAmount,
        string reservationId
    );

    constructor(uint256 _landTokenPrice, address _landContract) {
        owner = msg.sender;
        landContract = _landContract;
        landTokenPrice = _landTokenPrice;
        fundState = FundState.DISABLED;
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

    function fund(bytes memory data, bytes memory signature)
        public
        payable
        enabled
        validAmount
    {
        require(_verify(keccak256(data), signature, owner));
        (uint256 tokenId, uint256 expiry) = abi.decode(
            abi.encodePacked(data),
            (uint256, uint256)
        );
        addressToAmountFunded[msg.sender] += msg.value;
        Land(landContract).mint(msg.sender, tokenId);
        emit FundLandEvent(msg.sender, msg.value, "");
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
