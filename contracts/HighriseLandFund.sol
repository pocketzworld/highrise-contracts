// SPDX-License-Identifier: MIT

pragma solidity ^0.8.11;

contract HighriseLandFund {
    address public owner;

    // mapping to store which address deposited how much ETH
    mapping(address => uint256) public addressToAmountFunded;

    // mapping to store wallet owned tokens
    mapping(address => uint256[]) addressToLand;

    // whitelisted addresses
    mapping(address => bool) whitelistedAddresses;

    function getWalletTokens(address wallet)
        public
        view
        returns (uint256[] memory)
    {
        return addressToLand[wallet];
    }

    // token price in wei
    uint256 public landTokenPrice;

    enum FundState {
        ENABLED,
        DISABLED
    }

    FundState fundState;

    constructor(uint256 _landTokenPrice) {
        owner = msg.sender;
        landTokenPrice = _landTokenPrice;
        fundState = FundState.DISABLED;
    }

    modifier validTokens(uint256[] memory _landTokens) {
        require(
            _landTokens.length > 0 && _landTokens.length <= 4,
            "Maximum 4 tokens can be bought at once"
        );
        for (uint8 i = 0; i < _landTokens.length; i += 1) {
            bool found = false;
            for (uint8 j = 0; j < i; j += 1) {
                if (_landTokens[j] == _landTokens[i]) {
                    found = true;
                    break;
                }
            }
            require(!found, "Tokens not unique");
        }
        _;
    }

    modifier limitNotReached(uint256 tokens_length) {
        require(
            addressToLand[msg.sender].length + tokens_length <= 4,
            "Wallet already owns maximum amount of tokens"
        );
        _;
    }

    modifier validAmount(uint256 tokens_length) {
        require(
            msg.value >= landTokenPrice * tokens_length,
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

    function fund(uint256[] memory _landTokens)
        public
        payable
        enabled
        isWhitelisted(msg.sender)
        validTokens(_landTokens)
        limitNotReached(_landTokens.length)
        validAmount(_landTokens.length)
    {
        addressToAmountFunded[msg.sender] += msg.value;
        for (uint8 i = 0; i < _landTokens.length; i += 1) {
            addressToLand[msg.sender].push(_landTokens[i]);
        }
    }

    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    function enable() public payable onlyOwner {
        fundState = FundState.ENABLED;
    }

    function disable() public payable onlyOwner {
        fundState = FundState.DISABLED;
    }

    modifier disabled() {
        require(
            fundState == FundState.DISABLED,
            "Disable contract before withdrawing"
        );
        _;
    }

    function withdraw() public payable onlyOwner disabled {
        payable(msg.sender).transfer(address(this).balance);
    }

    function addUser(address _addressToWhitelist) public onlyOwner {
        whitelistedAddresses[_addressToWhitelist] = true;
    }

    function verifyUser(address _whitelistedAddress)
        public
        view
        returns (bool)
    {
        bool userIsWhitelisted = whitelistedAddresses[_whitelistedAddress];
        return userIsWhitelisted;
    }

    modifier isWhitelisted(address _address) {
        require(whitelistedAddresses[_address], "You need to be whitelisted");
        _;
    }
}
