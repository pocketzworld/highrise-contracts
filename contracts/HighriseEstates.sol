// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/utils/ERC721Holder.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "./HighriseLand.sol";

contract HighriseEstates is ERC721Enumerable, ERC721Holder {
    using Counters for Counters.Counter;

    address public land;
    Counters.Counter private _tokenIds;
    mapping(uint256 => uint256[]) public estatesToParcels;

    constructor(
        string memory _name,
        string memory _symbol,
        address _land
    ) ERC721(_name, _symbol) {
        land = _land;
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
        uint256[] memory tokens;

        for (uint256 i = 0; i < balance; i++) {
            tokens[i] = tokenOfOwnerByIndex(owner, i);
        }

        return tokens;
    }

    function _isEstateShapeValid(uint256[] memory parcelIds)
        internal
        returns (bool)
    {
        if (parcelIds.length == 9) {
            // We expect a 3x3 matrix.
            // X checks
            require(
                parseToCoordinates(parcelIds[0])[0] + 1 ==
                    parseToCoordinates(parcelIds[1])[0]
            );
            require(
                parseToCoordinates(parcelIds[1])[0] + 1 ==
                    parseToCoordinates(parcelIds[2])[0]
            );
            require(
                parseToCoordinates(parcelIds[3])[0] + 1 ==
                    parseToCoordinates(parcelIds[4])[0]
            );
            require(
                parseToCoordinates(parcelIds[4])[0] + 1 ==
                    parseToCoordinates(parcelIds[5])[0]
            );
            require(
                parseToCoordinates(parcelIds[6])[0] + 1 ==
                    parseToCoordinates(parcelIds[7])[0]
            );
            require(
                parseToCoordinates(parcelIds[7])[0] + 1 ==
                    parseToCoordinates(parcelIds[8])[0]
            );
            // Y checks
            require(
                parseToCoordinates(parcelIds[0])[1] ==
                    parseToCoordinates(parcelIds[1])[1]
            );
            require(
                parseToCoordinates(parcelIds[1])[1] ==
                    parseToCoordinates(parcelIds[2])[1]
            );
            require(
                parseToCoordinates(parcelIds[3])[1] ==
                    parseToCoordinates(parcelIds[4])[1]
            );
            require(
                parseToCoordinates(parcelIds[4])[1] ==
                    parseToCoordinates(parcelIds[5])[1]
            );
            require(
                parseToCoordinates(parcelIds[6])[1] ==
                    parseToCoordinates(parcelIds[7])[1]
            );
            require(
                parseToCoordinates(parcelIds[7])[1] ==
                    parseToCoordinates(parcelIds[8])[1]
            );
            return true;
        } else if (parcelIds.length == 36) {
            return true;
        } else if (parcelIds.length == 81) {
            return true;
        } else if (parcelIds.length == 144) {
            return true;
        }
        return false;
    }

    function mintFromParcels(uint256[] memory tokenIds)
        public
        returns (uint256)
    {
        require(
            _isEstateShapeValid(tokenIds),
            "Invalid estate shape, must be square."
        );
        Land(land).bindToEstate(msg.sender, tokenIds);
        _tokenIds.increment();
        uint256 tokenId = _tokenIds.current();
        estatesToParcels[tokenId] = tokenIds;
        _mint(msg.sender, tokenId);
        return tokenId;
    }

    function burn(uint256 tokenId) public {
        require(
            _exists(tokenId),
            "ERC721: operator query for nonexistent token"
        );
        require(
            _isApprovedOrOwner(msg.sender, tokenId),
            "ERC721Burnable: caller is not owner nor approved"
        );
        uint256[] memory parcels = estatesToParcels[tokenId];
        for (uint256 i = 0; i < parcels.length; i++) {
            Land(land).safeTransferFrom(address(this), msg.sender, parcels[i]);
        }
        _burn(tokenId);
    }
}
