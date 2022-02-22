// SPDX-License-Identifier: MIT

pragma solidity ^0.8.4;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

abstract contract Land is ERC721Enumerable {
    function bindToEstate(address owner, uint256[] memory tokenIds)
        public
        virtual;

    function mint(address user, uint256 tokenId) public virtual;
}

function parseToCoordinates(uint256 tokenId) pure returns (uint256[2] memory) {
    return [tokenId >> 24, tokenId & 0xFFFFFF];
}

contract HighriseLand is AccessControl, Land {
    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual
        override(ERC721Enumerable, AccessControl)
        returns (bool)
    {
        return true;
    }

    bytes32 public constant ESTATE_MANAGER_ROLE = keccak256("ESTATE_MANAGER");
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    constructor(
        string memory _name,
        string memory _symbol,
        address _imx
    ) ERC721(_name, _symbol) {
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(MINTER_ROLE, msg.sender);
    }

    function bindToEstate(address owner, uint256[] memory tokenIds)
        public
        override
        onlyRole(ESTATE_MANAGER_ROLE)
    {
        for (uint256 i = 0; i < tokenIds.length; i++) {
            _safeTransfer(owner, msg.sender, tokenIds[i], bytes(""));
        }
    }

    function mint(address user, uint256 tokenId)
        public
        override
        onlyRole(MINTER_ROLE)
    {
        _safeMint(user, tokenId);
    }

    function _mintFor(
        address user,
        uint256 tokenId,
        bytes memory blueprint
    ) internal {
        _safeMint(user, tokenId, blueprint);
    }

    function _baseURI() internal view override returns (string memory) {
        return "s3://highrise-land/metadata/";
    }

    function tokensOfOwner(address owner)
        public
        view
        returns (uint256[] memory)
    {
        uint256 balance = balanceOf(owner);
        uint256[] memory tokens = new uint256[](balance);

        for (uint256 i = 0; i < balance; i++) {
            tokens[i] = tokenOfOwnerByIndex(owner, i);
        }

        return tokens;
    }
}
